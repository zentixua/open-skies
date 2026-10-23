#!/usr/bin/env python3
"""Сборка запускается на новом месте: выделенный сервер — до «Done», клиент — до входа в мир. Шаг CI и проверка руками.

  python3 tools/boot_check.py server run/boot/server
  python3 tools/boot_check.py client run/boot/client --world run/boot/server/world \
      [--wrap 'xvfb-run -a -s "-screen 0 1280x720x24" {cmd}']

Всё ставится так же, как у игрока и на сервере, с нуля: NeoForge — версии из pack.toml (сервер — установщиком
NeoForge, клиент — portablemc: Minecraft, библиотеки и ассеты Mojang), моды и config/ — packwiz-installer из pack/,
отданной по HTTP на 127.0.0.1 (сервер — `-s server`, клиент — `-s client`; необязательные — как их галочка
по умолчанию). Каталог должен быть новым: смешивать с прежним набором модов нельзя.

Сервер слушает только 127.0.0.1, без проверки лицензии; после «Done» получает `stop` и должен выйти с кодом 0.
Клиент входит в мир --world (копия в saves/) через Quick Play и должен прожить в нём --stay секунд без падения;
потом процесс гасится. Шейдерпак, который выбирает `config/iris.properties` сборки, Iris должен найти и прочитать
(строка «Using shaderpack: <имя>» в логе; пак читается до сборки шейдеров на видеокарте): имя в настройке и `filename`
шейдерпака в pack/shaderpacks/ расходиться не могут. Окно клиенту нужно: на машине без экрана — --wrap с xvfb-run
(CI) или вложенным KWin (ноутбук: tools/nested_kwin.sh incoming, `{cmdq}` — команда одним аргументом). Звук клиент
открыть не должен (на ноутбуке его закрывает nested_kwin.sh, в CI устройства нет).

Падение загрузки (мод не принял NeoForge или другой мод, «Mod loading has failed», ошибка в RegisterEvent) — код 1,
в конце — хвост лога и отчёт о падении. Что нужно: Java 21 (JAVA_HOME или java в PATH), для клиента — portablemc 5
(PORTABLEMC или portablemc в PATH).
"""
import argparse
import functools
import http.server
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
# загрузчик packwiz-installer и сам установщик — закреплённые версии: проверка не меняется сама от их выпусков
BOOTSTRAP = "https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar"
INSTALLER = "https://github.com/packwiz/packwiz-installer/releases/download/v0.5.14/packwiz-installer.jar"
NEOFORGE = "https://maven.neoforged.net/releases/net/neoforged/neoforge/{v}/neoforge-{v}-installer.jar"
DONE = re.compile(r"\]: Done \([0-9.]+s\)!")
JOINED = re.compile(r"\]: (\S+) joined the game")
FAILED = re.compile(r"Mod loading has failed|Loading errors encountered|Preparing crash report|Failed to start the minecraft server")


def java():
    home = os.environ.get("JAVA_HOME")
    exe = os.path.join(home, "bin", "java") if home else shutil.which("java")
    if not exe or not os.path.exists(exe):
        sys.exit("нет Java 21: JAVA_HOME или java в PATH")
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
                sys.exit(f"не скачать {url}: {e}")
            time.sleep(2 << attempt)
    raise AssertionError("недостижимо")


def pack_versions():
    with open(os.path.join(PACK, "pack.toml"), "rb") as f:
        pack = tomllib.load(f)
    return pack["version"], pack["versions"]["minecraft"], pack["versions"]["neoforge"]


@functools.cache
def serve_pack():
    """pack/ по HTTP на 127.0.0.1 — адрес pack.toml для packwiz-installer (как raw.githubusercontent.com у игроков)."""
    handler = functools.partial(QuietHandler, directory=PACK)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}/pack.toml"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 — имя параметра как у BaseHTTPRequestHandler
        pass


def install_pack(dest, side, cache):
    """packwiz-installer без окна (-g) ставит pack/ в dest: моды стороны side и config/."""
    jar = os.path.join(dest, "packwiz-installer-bootstrap.jar")
    shutil.copyfile(download(BOOTSTRAP, os.path.join(cache, "packwiz-installer-bootstrap-0.0.3.jar")), jar)
    shutil.copyfile(download(INSTALLER, os.path.join(cache, "packwiz-installer-0.5.14.jar")),
                    os.path.join(dest, "packwiz-installer.jar"))
    run([java(), "-jar", jar, "--bootstrap-no-update", "-g", "-s", side, serve_pack()], dest, "packwiz-installer")
    mods = sorted(f for f in os.listdir(os.path.join(dest, "mods")) if f.endswith(".jar"))
    print(f"packwiz-installer ({side}): модов {len(mods)}")
    return mods


def run(argv, cwd, what):
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        print(p.stdout[-4000:])
        sys.exit(f"{what}: код {p.returncode}")
    return p.stdout


def fresh(dest):
    dest = os.path.abspath(dest)
    if os.path.isdir(os.path.join(dest, "mods")):
        sys.exit(f"в {dest} уже есть mods/ — нужен новый каталог")
    os.makedirs(dest, exist_ok=True)
    return dest


def report(dest, log):
    """Хвост лога и отчёт о падении — в вывод проверки (в CI — в лог шага)."""
    if os.path.isfile(log):
        with open(log, errors="replace") as f:
            lines = f.readlines()
        print("".join(lines[-80:]))
    crashes = os.path.join(dest, "crash-reports")
    if os.path.isdir(crashes):
        for name in sorted(os.listdir(crashes)):
            with open(os.path.join(crashes, name), errors="replace") as f:
                print(f"==== {name}\n" + f.read()[:12000])


def selected_shaderpack(dest):
    """Шейдерпак, который Iris должен включить по config/iris.properties экземпляра; None — шейдеры не выбраны.
    Читать до запуска: игра файл переписывает — Voxy выключает шейдеры, если его отрисовка с ними не встала
    (IrisUtil.disableIrisShaders; в CI так и есть: Voxy нужна OpenGL 4.6, у llvmpipe 4.5)."""
    path = os.path.join(dest, "config", "iris.properties")
    if not os.path.isfile(path):
        return None
    props = {}
    with open(path, encoding="latin-1") as f:  # формат java.util.Properties — ISO-8859-1
        for line in f:
            line = line.strip()
            if line and line[0] not in "#!" and "=" in line:
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    if props.get("enableShaders") == "false":
        return None
    return props.get("shaderPack") or None


def wait_for(proc, log, pattern, timeout):
    """Ждать строку pattern в логе, пока процесс жив; None — процесс вышел, вышел срок или загрузка упала."""
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
    """Процесс и всё, что он запустил (обёртка, JVM), — TERM, через 20 с KILL."""
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
    print(f"Open Skies {version}: сервер, Minecraft {mc}, NeoForge {neo} → {dest}")
    installer = download(NEOFORGE.format(v=neo), os.path.join(a.cache, f"neoforge-{neo}-installer.jar"))
    run([java(), "-jar", installer, "--install-server", dest], dest, "установщик NeoForge")
    install_pack(dest, "server", a.cache)
    with open(os.path.join(dest, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    # только петля и порт 0 нельзя (сервер его не берёт) — свободный порт от системы
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    with open(os.path.join(dest, "server.properties"), "w") as f:
        f.write(f"server-ip=127.0.0.1\nserver-port={port}\nonline-mode=false\nlevel-seed={a.seed}\n"
                "spawn-protection=0\nmotd=Open Skies boot check\n")
    args = os.path.join("libraries", "net", "neoforged", "neoforge", neo, "unix_args.txt")
    argv = [java(), f"-Xmx{a.memory}", f"@{args}", "nogui"]
    log = os.path.join(dest, "logs", "latest.log")
    started = time.monotonic()
    with open(os.path.join(dest, "console.log"), "w") as out:
        proc = subprocess.Popen(argv, cwd=dest, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT,
                                text=True, start_new_session=True)
        done = wait_for(proc, log, DONE, a.timeout)
        if not done:
            stop_group(proc)
            report(dest, log)
            sys.exit(f"сервер не дошёл до «Done» (код {proc.returncode}, {time.monotonic() - started:.0f} с)")
        print(f"сервер: «Done» за {time.monotonic() - started:.0f} с от запуска")
        assert proc.stdin is not None
        proc.stdin.write("stop\n")
        proc.stdin.flush()
        try:
            code = proc.wait(a.timeout)
        except subprocess.TimeoutExpired:
            stop_group(proc)
            report(dest, log)
            sys.exit("сервер не остановился по stop")
    if code != 0:
        report(dest, log)
        sys.exit(f"сервер вышел с кодом {code}")
    print("сервер: остановлен, код 0")


def client(a):
    dest = fresh(a.dir)
    version, mc, neo = pack_versions()
    print(f"Open Skies {version}: клиент, Minecraft {mc}, NeoForge {neo} → {dest}")
    pmc = os.environ.get("PORTABLEMC") or shutil.which("portablemc")
    if not pmc:
        sys.exit("нет portablemc 5 (pip install portablemc): PORTABLEMC или portablemc в PATH")
    main_dir = os.path.abspath(os.path.join(a.cache, "minecraft"))
    base = [pmc, "--main-dir", main_dir, "--output", "machine", "start", "--jvm", java(), f"neoforge::{neo}"]
    run(base[:5] + ["start", "--dry"] + base[6:], dest, "portablemc: Minecraft и NeoForge")
    install_pack(dest, "client", a.cache)
    shaderpack = selected_shaderpack(dest)
    # без экрана приветствия (иначе Quick Play ждёт за ним вечно) и без паузы, когда окно не в фокусе
    with open(os.path.join(dest, "options.txt"), "w") as f:
        f.write("onboardAccessibility:false\npauseOnLostFocus:false\nsoundCategory_master:0.0\n")
    world = os.path.basename(os.path.normpath(a.world))
    shutil.copytree(a.world, os.path.join(dest, "saves", world))
    argv = base[:-1] + ["--mc-dir", dest, "--username", a.user, "--resolution", "1280x720", "--join-world", world,
                        f"--jvm-arg=-Xmx{a.memory}", base[-1]]
    cmd = shlex.join(argv)
    if a.wrap:
        cmd = a.wrap.replace("{cmdq}", shlex.quote(cmd)).replace("{cmd}", cmd)
    # та же команда — для повтора руками (тот же каталог, тот же мир)
    with open(os.path.join(dest, "launch.sh"), "w") as f:
        f.write(f"#!/bin/sh\ncd {shlex.quote(dest)} && exec {cmd}\n")
    os.chmod(os.path.join(dest, "launch.sh"), 0o755)
    log = os.path.join(dest, "logs", "latest.log")
    started = time.monotonic()
    with open(os.path.join(dest, "console.log"), "w") as out:
        proc = subprocess.Popen(cmd, shell=True, cwd=dest, stdout=out, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            joined = wait_for(proc, log, JOINED, a.timeout)
            if not joined:
                stop_group(proc)
                report(dest, log)
                sys.exit(f"клиент не вошёл в мир (код {proc.returncode}, {time.monotonic() - started:.0f} с)")
            print(f"клиент: {joined.group(1)} в мире «{world}» через {time.monotonic() - started:.0f} с от запуска")
            # в мире — ещё --stay секунд: рисуются чанки, встают моды, которые начинают работу с миром
            end = time.monotonic() + a.stay
            while time.monotonic() < end:
                with open(log, errors="replace") as f:
                    crashed = FAILED.search(f.read())
                if crashed or proc.poll() is not None:
                    stop_group(proc)
                    report(dest, log)
                    sys.exit(f"клиент упал в мире (код {proc.returncode})")
                time.sleep(1)
        finally:
            stop_group(proc)
    print(f"клиент: {a.stay} с в мире без падения")
    if shaderpack:
        with open(log, errors="replace") as f:
            if f"Using shaderpack: {shaderpack}" not in f.read():
                report(dest, log)
                sys.exit(f"Iris не прочитал шейдерпак «{shaderpack}» из config/iris.properties (нет такого файла в "
                         "shaderpacks/ или пак не читается)")
        print(f"клиент: Iris прочитал шейдерпак «{shaderpack}»")
        if selected_shaderpack(dest) is None:
            # не падение: так бывает на машине без нужной Voxy OpenGL — в вывод, чтобы причина была видна
            print("клиент: за время игры шейдеры в config/iris.properties выключены; в логе:")
            with open(log, errors="replace") as f:
                hits = [line for line in f if re.search(r"(?i)voxy.*(error|fail|exception)|shaders are disabled", line)]
            print("".join(hits[:10]), end="")


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="what", required=True)
    for name in ("server", "client"):
        p = sub.add_parser(name)
        p.add_argument("dir", help="каталог (новый)")
        p.add_argument("--cache", default=os.path.join(ROOT, "run", "boot-cache"),
                       help="скачанное: установщики, Minecraft клиента (второй раз не качается)")
        p.add_argument("--timeout", type=int, default=900, help="секунд на загрузку")
        p.add_argument("--memory", default="4G", help="-Xmx")
    sub.choices["server"].add_argument("--seed", default="open-skies", help="зерно мира проверки")
    c = sub.choices["client"]
    c.add_argument("--world", required=True, help="каталог мира (например world сервера проверки)")
    c.add_argument("--user", default="BootCheck")
    c.add_argument("--stay", type=int, default=30, help="секунд в мире после входа")
    c.add_argument("--wrap", help="оболочка запуска: {cmd} — команда, {cmdq} — она же одним аргументом")
    a = ap.parse_args()
    a.cache = os.path.abspath(a.cache)
    (server if a.what == "server" else client)(a)


if __name__ == "__main__":
    main()
