#!/usr/bin/env python3
"""Boot the pack in a fresh location: server to "Done", client to world entry. CI step and manual check.

  python3 tools/boot_check.py server run/boot/server
  python3 tools/boot_check.py client run/boot/client --world run/boot/server/world \
      [--wrap 'xvfb-run -a -s "-screen 0 1280x720x24" {cmd}']
  python3 tools/boot_check.py client run/boot/record --server run/boot/server [--wrap …]

Everything is installed from scratch, just as for a player and on the server: NeoForge versions from pack.toml
(server: NeoForge installer; client: portablemc installs Minecraft, Mojang libraries and assets), mods and config/
via packwiz-installer from pack/, served over HTTP on 127.0.0.1 (server: `-s server`, client: `-s client`; optional
mods follow their default checkbox). The directory must be new: do not mix with an earlier set of mods.

The server listens only on 127.0.0.1, with account verification disabled; after "Done", it receives `stop` and must
exit with code 0. The client enters --world (copied into saves/) through Quick Play and must stay there for --stay
seconds without crashing; then its process is terminated. With --server, the client joins the dedicated check
server (same directory, server started again) with recording mods, and Flashback records a replay from the first
join next to a sleeping villager (SLEEPER). This checks what singleplayer cannot: server registries and joining
with the server mods' channels. The client needs a window: on a headless machine, use --wrap with xvfb-run (CI)
or nested KWin (laptop: tools/nested_kwin.sh incoming, `{cmdq}` passes the command as one argument). The client must
not open an audio device (nested_kwin.sh blocks it on the laptop; CI has no device).

A loading crash (a mod rejects NeoForge or another mod, "Mod loading has failed", a RegisterEvent error) exits
with code 1 and prints the log tail and crash report at the end. Requirements: Java 21 (JAVA_HOME or java in PATH);
for the client, portablemc 5 (PORTABLEMC or portablemc in PATH).
"""
import argparse
import functools
import hashlib
import http.server
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack")
USER_AGENT = "zentixua/open-skies tools/boot_check.py"
# Pin both packwiz-installer's bootstrap and the installer: their releases must not change the check automatically.
BOOTSTRAP = "https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar"
INSTALLER = "https://github.com/packwiz/packwiz-installer/releases/download/v0.5.14/packwiz-installer.jar"
NEOFORGE = "https://maven.neoforged.net/releases/net/neoforged/neoforge/{v}/neoforge-{v}-installer.jar"
# Replay recording mods (optional in pack/) for the client check on the server.
RECORDING = ("connector", "flashback", "flashback-neoforge-fixed")
# Server scene before the client joins: the player spawns on a platform in the sky next to a sleeping villager
# (no AI, so it sleeps throughout the check). Client mods play sleep sounds (Subtle Effects snoring), recorded by Flashback.
SLEEPER = (
    "forceload add -16 -16 15 15", "gamerule doDaylightCycle false", "gamerule doMobSpawning false",
    "gamerule spawnRadius 0", "time set 18000", "defaultgamemode creative",
    "fill -4 199 -4 4 199 4 stone",
    "setblock 0 200 0 red_bed[facing=north,part=foot]", "setblock 0 200 -1 red_bed[facing=north,part=head]",
    "summon villager 0 200.5625 -1 {NoAI:1b,SleepingX:0,SleepingY:200,SleepingZ:-1}",
    "setworldspawn 2 200 2",
)
SUMMONED = re.compile(r"\]: Summoned new ")
DONE = re.compile(r"\]: Done \([0-9.]+s\)!")
JOINED = re.compile(r"\]: (\S+) joined the game")
# Disconnecting from the server ends Flashback recording (automaticallyFinish); its directory remains until saving.
LEFT = re.compile(r"\]: \S+ lost connection: (.*)")
# "Unreported exception thrown!": client crash outside the main loop (Flashback recording thread); the report comes later.
FAILED = re.compile(r"Mod loading has failed|Loading errors encountered|Preparing crash report|"
                    r"Failed to start the minecraft server|Unreported exception thrown!")


def java():
    home = os.environ.get("JAVA_HOME")
    exe = os.path.join(home, "bin", "java") if home else shutil.which("java")
    if not exe or not os.path.exists(exe):
        sys.exit("Java 21 not found: JAVA_HOME or java in PATH")
    return exe


def download(url, dest) -> str:
    if os.path.isfile(dest):
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as out:
                shutil.copyfileobj(r, out)
            os.replace(dest + ".part", dest)
            return dest
        except OSError as e:
            if attempt == 3:
                sys.exit(f"cannot download {url}: {e}")
            time.sleep(2 << attempt)
    raise AssertionError("unreachable")


def pack_versions():
    with open(os.path.join(PACK, "pack.toml"), "rb") as f:
        pack = tomllib.load(f)
    return pack["version"], pack["versions"]["minecraft"], pack["versions"]["neoforge"]


@functools.cache
def serve_pack():
    """Serve pack/ over HTTP on 127.0.0.1: pack.toml URL for packwiz-installer (like raw.githubusercontent.com for players)."""
    handler = functools.partial(QuietHandler, directory=PACK)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}/pack.toml"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 — parameter name matches BaseHTTPRequestHandler.
        pass


def install_pack(dest, side, cache):
    """Headless packwiz-installer (-g) installs pack/ into dest: mods for side and config/."""
    jar = os.path.join(dest, "packwiz-installer-bootstrap.jar")
    shutil.copyfile(download(BOOTSTRAP, os.path.join(cache, "packwiz-installer-bootstrap-0.0.3.jar")), jar)
    shutil.copyfile(download(INSTALLER, os.path.join(cache, "packwiz-installer-0.5.14.jar")),
                    os.path.join(dest, "packwiz-installer.jar"))
    run([java(), "-jar", jar, "--bootstrap-no-update", "-g", "-s", side, serve_pack()], dest, "packwiz-installer")
    mods = sorted(f for f in os.listdir(os.path.join(dest, "mods")) if f.endswith(".jar"))
    print(f"packwiz-installer ({side}): {len(mods)} mods")
    return mods


def run(argv, cwd, what):
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        print(p.stdout[-4000:])
        sys.exit(f"{what}: exit code {p.returncode}")
    return p.stdout


def fresh(dest):
    dest = os.path.abspath(dest)
    if os.path.isdir(os.path.join(dest, "mods")):
        sys.exit(f"{dest} already contains mods/ — a new directory is required")
    os.makedirs(dest, exist_ok=True)
    return dest


def report(dest, log):
    """Print the log tail and crash report in the check output (the step log in CI)."""
    if os.path.isfile(log):
        with open(log, errors="replace") as f:
            lines = f.readlines()
        print("".join(lines[-80:]))
    crashes = os.path.join(dest, "crash-reports")
    if os.path.isdir(crashes):
        for name in sorted(os.listdir(crashes)):
            with open(os.path.join(crashes, name), errors="replace") as f:
                print(f"==== {name}\n" + f.read()[:12000])


def wait_for(proc, log, pattern, timeout):
    """Wait for pattern in the log while the process is alive; None on exit, timeout or loading failure."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if os.path.isfile(log):
            with open(log, errors="replace") as f:
                text = f.read()
            if FAILED.search(text):
                return None
            m = pattern.search(text)
            if m:
                return m
        if proc.poll() is not None:
            return None
        time.sleep(1)
    return None


def stop_group(proc):
    """Send TERM to the process and its children (wrapper, JVM), then KILL after 20 s."""
    for sig, wait in ((signal.SIGTERM, 20), (signal.SIGKILL, 10)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(wait)
            return
        except subprocess.TimeoutExpired:
            pass


def server(a):
    dest = fresh(a.dir)
    version, mc, neo = pack_versions()
    print(f"Open Skies {version}: server, Minecraft {mc}, NeoForge {neo} → {dest}")
    installer = download(NEOFORGE.format(v=neo), os.path.join(a.cache, f"neoforge-{neo}-installer.jar"))
    run([java(), "-jar", installer, "--install-server", dest], dest, "NeoForge installer")
    install_pack(dest, "server", a.cache)
    with open(os.path.join(dest, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    # Loopback only; the server does not accept port 0, so ask the OS for a free port.
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    with open(os.path.join(dest, "server.properties"), "w") as f:
        f.write(f"server-ip=127.0.0.1\nserver-port={port}\nonline-mode=false\nlevel-seed={a.seed}\n"
                "spawn-protection=0\nmotd=Open Skies boot check\n")
    proc, log = start_server(dest, neo, a.memory, a.timeout)
    stop_server(proc, dest, log, a.timeout)


def start_server(dest, neo, memory, timeout):
    """Boot the installed check server to "Done"; return its process with console stdin and the log path."""
    args = os.path.join("libraries", "net", "neoforged", "neoforge", neo, "unix_args.txt")
    argv = [java(), f"-Xmx{memory}", f"@{args}", "nogui"]
    log = os.path.join(dest, "logs", "latest.log")
    # The previous run's log (server check before --server) already says "Done": move it aside to wait for a new one.
    if os.path.isfile(log):
        os.replace(log, os.path.join(dest, "logs", "previous-run.log"))
    started = time.monotonic()
    with open(os.path.join(dest, "console.log"), "a") as out:
        proc = subprocess.Popen(argv, cwd=dest, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT,
                                text=True, start_new_session=True)
    done = wait_for(proc, log, DONE, timeout)
    if not done:
        stop_group(proc)
        report(dest, log)
        sys.exit(f"server did not reach 'Done' (exit code {proc.returncode}, {time.monotonic() - started:.0f} s)")
    print(f"server: 'Done' {time.monotonic() - started:.0f} s after launch")
    return proc, log


def console(proc, *commands):
    assert proc.stdin is not None
    for c in commands:
        proc.stdin.write(c + "\n")
        proc.stdin.flush()


def stop_server(proc, dest, log, timeout):
    console(proc, "stop")
    try:
        code = proc.wait(timeout)
    except subprocess.TimeoutExpired:
        stop_group(proc)
        report(dest, log)
        sys.exit("server did not shut down after stop")
    if code != 0:
        report(dest, log)
        sys.exit(f"server exited with code {code}")
    print("server: stopped, exit code 0")


def client(a):
    dest = fresh(a.dir)
    version, mc, neo = pack_versions()
    print(f"Open Skies {version}: client, Minecraft {mc}, NeoForge {neo} → {dest}")
    pmc = os.environ.get("PORTABLEMC") or shutil.which("portablemc")
    if not pmc:
        sys.exit("portablemc 5 not found (pip install portablemc): PORTABLEMC or portablemc in PATH")
    main_dir = os.path.abspath(os.path.join(a.cache, "minecraft"))
    base = [pmc, "--main-dir", main_dir, "--output", "machine", "start", "--jvm", java(), f"neoforge::{neo}"]
    run(base[:5] + ["start", "--dry"] + base[6:], dest, "portablemc: Minecraft and NeoForge")
    install_pack(dest, "client", a.cache)
    # Skip the welcome screen (otherwise Quick Play waits behind it forever) and pausing when the window loses focus.
    options = "onboardAccessibility:false\npauseOnLostFocus:false\nsoundCategory_master:0.0\n"
    if a.server:
        install_recording(dest)
        # Skip the "online play is not controlled by Mojang" warning (otherwise joining waits behind it forever).
        options += "skipMultiplayerWarning:true\n"
    with open(os.path.join(dest, "options.txt"), "w") as f:
        f.write(options)
    if a.server:
        srv = os.path.abspath(a.server)
        with open(os.path.join(srv, "server.properties")) as f:
            port = re.search(r"^server-port=(\d+)$", f.read(), re.M).group(1)
        target = ["--join-server", "127.0.0.1", "--join-server-port", port]
        where = "on the check server"
    else:
        world = os.path.basename(os.path.normpath(a.world))
        shutil.copytree(a.world, os.path.join(dest, "saves", world))
        target = ["--join-world", world]
        where = f"in world '{world}'"
    argv = base[:-1] + ["--mc-dir", dest, "--username", a.user, "--resolution", "1280x720", *target,
                        f"--jvm-arg=-Xmx{a.memory}", base[-1]]
    cmd = shlex.join(argv)
    if a.wrap:
        cmd = a.wrap.replace("{cmdq}", shlex.quote(cmd)).replace("{cmd}", cmd)
    # The same command for a manual rerun (same directory, same world or server).
    with open(os.path.join(dest, "launch.sh"), "w") as f:
        f.write(f"#!/bin/sh\ncd {shlex.quote(dest)} && exec {cmd}\n")
    os.chmod(os.path.join(dest, "launch.sh"), 0o755)
    server_proc = server_log = None
    if a.server:
        server_proc, server_log = start_server(srv, neo, a.server_memory, a.timeout)
        console(server_proc, *SLEEPER)
        if not wait_for(server_proc, server_log, SUMMONED, 60):
            stop_group(server_proc)
            report(srv, server_log)
            sys.exit("server did not set up the sleeping villager scene")
    log = os.path.join(dest, "logs", "latest.log")
    started = time.monotonic()
    try:
        with open(os.path.join(dest, "console.log"), "w") as out:
            proc = subprocess.Popen(cmd, shell=True, cwd=dest, stdout=out, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        try:
            # Joining appears in the world host's log: the client in singleplayer, otherwise the server.
            joined = wait_for(proc, server_log or log, JOINED, a.timeout)
            if not joined:
                stop_group(proc)
                report(dest, log)
                sys.exit(f"client did not join (exit code {proc.returncode}, {time.monotonic() - started:.0f} s)")
            print(f"client: {joined.group(1)} {where} {time.monotonic() - started:.0f} s after launch")
            # Stay in the world for --stay more seconds: render chunks and start mods that need a loaded world.
            end = time.monotonic() + a.stay
            while time.monotonic() < end:
                with open(log, errors="replace") as f:
                    text = f.read()
                crashed = FAILED.search(text)
                if server_log:
                    with open(server_log, errors="replace") as f:
                        left = LEFT.search(f.read())
                    if left:
                        stop_group(proc)
                        report(dest, log)
                        sys.exit(f"client disconnected from the server: {left.group(1)}")
                if crashed or proc.poll() is not None:
                    stop_group(proc)
                    report(dest, log)
                    sys.exit(f"client crashed {where} (exit code {proc.returncode})")
                time.sleep(1)
            if a.server:
                recording = os.path.join(dest, "flashback", "temp", "recording")
                if not (os.path.isdir(recording) and os.listdir(recording)):
                    report(dest, log)
                    sys.exit("Flashback did not start recording")
        finally:
            stop_group(proc)
    finally:
        if server_proc:
            stop_server(server_proc, srv, server_log, a.timeout)
    print(f"client: {a.stay} s {where} without crashing" + (", Flashback was recording" if a.server else ""))


def install_recording(dest):
    """Recording mods (Flashback and its requirements: optional, disabled by default) and recording from the first join.

    The server check does not need Voxy or Roxy (the singleplayer check loads them). With Mesa llvmpipe alongside
    the server, they exhaust the CI machine's memory, so they are excluded here."""
    for name in RECORDING:
        with open(os.path.join(PACK, "mods", f"{name}.pw.toml"), "rb") as f:
            meta = tomllib.load(f)
        jar = download(meta["download"]["url"], os.path.join(dest, "mods", meta["filename"]))
        assert meta["download"]["hash-format"] == "sha512"
        with open(jar, "rb") as f:
            if hashlib.sha512(f.read()).hexdigest() != meta["download"]["hash"]:
                sys.exit(f"{meta['filename']}: hash does not match pack/")
    for jar in os.listdir(os.path.join(dest, "mods")):
        if jar.startswith(("voxy-", "roxy-")):
            os.remove(os.path.join(dest, "mods", jar))
    os.makedirs(os.path.join(dest, "config", "flashback"), exist_ok=True)
    with open(os.path.join(dest, "config", "flashback", "flashback.json"), "w") as f:
        json.dump({"configVersion": 2, "recordingControls": {"automaticallyStart": True}}, f)


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="what", required=True)
    for name in ("server", "client"):
        p = sub.add_parser(name)
        p.add_argument("dir", help="directory (new)")
        p.add_argument("--cache", default=os.path.join(ROOT, "run", "boot-cache"),
                       help="downloads: installers and client Minecraft (not downloaded again)")
        p.add_argument("--timeout", type=int, default=900, help="seconds allowed for startup")
        p.add_argument("--memory", default="4G", help="-Xmx")
    sub.choices["server"].add_argument("--seed", default="open-skies", help="check world seed")
    c = sub.choices["client"]
    where = c.add_mutually_exclusive_group(required=True)
    where.add_argument("--world", help="world directory (e.g. the check server's world): singleplayer")
    where.add_argument("--server", help="check server directory: the client joins and records a Flashback replay "
                                        "next to a sleeping villager")
    c.add_argument("--server-memory", default="3G", help="server -Xmx with --server")
    c.add_argument("--user", default="BootCheck")
    c.add_argument("--stay", type=int, default=30, help="seconds in the world after joining")
    c.add_argument("--wrap", help="launch wrapper: {cmd} is the command, {cmdq} is the same command as one argument")
    a = ap.parse_args()
    a.cache = os.path.abspath(a.cache)
    (server if a.what == "server" else client)(a)


if __name__ == "__main__":
    main()
