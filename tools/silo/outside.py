# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "numpy"]
# ///
"""The dead outside of the series' present day on the silo server: overcast, dust, dead colour, no rain.

Switched by Artem in game, a few minutes after a nuke:

  /function silo:outside/on      overcast that stays (weather rain, weather cycle held), dead biomes near players
  /function silo:outside/off     clear weather and the weather cycle as it was; every biome back as it was

How (plan and reasons: the silo-weather report):
- Rain gives the overcast: grey sky, sun hidden, flat dim light; every shaderpack reads it (rainStrength).
- No rain falls because the outside's biomes are swapped for "dead twins": exact copies of each overworld biome
  (`silo:dead/<namespace>/<path>`) without precipitation and with the colours measured from the series' frames
  (sky, fog, grass, leaves, water) and a drifting dust particle. Rain over a biome without precipitation renders as
  overcast without rain: no streaks or sound; Complementary's dry-biome fog, Photon's overcast, Particle Rain's dust
  haze on sand/coarse dirt.
- An Almighty rule (persisted with the world) swaps biomes in the chunks players already see, nearest first, within
  a small time budget: original -> twin while on, twin -> original while off. Each twin maps to one original, so off
  restores exactly. It never loads a chunk; chunks never visited again are swapped when a player next sees them.
  Incoming withholds a chunk of its ruin zone from players until its ruin plan (with scorched biomes) is applied, so
  the rule only ever sees Incoming's finished tiers: incoming:singed/scorched/charred get twins too.
- Cells below the chunk's lowest surface minus 8 blocks keep their biome: the silos inside stay as they are.

Subcommands (bridge: ALMIGHTY_URL, ALMIGHTY_TOKEN_FILE, as build_live.Bridge):
  uv run tools/silo/outside.py dump OUT.json                 overworld biomes of the running server, as datapack JSON
  uv run tools/silo/outside.py pack DUMP.json OUT_DIR        datapack silo_outside (twins, functions, GM note)
  uv run tools/silo/outside.py rule install|remove|status    the Almighty rule
  uv run tools/silo/outside.py census X Z R                  biome cells in loaded chunks within R chunks of X Z
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NS = "silo"
PREFIX = "dead/"
RULE = "silo-outside"

# Colours of the dead outside. Targets are the on-screen means of the series' present-day outside frames
# (silo-research/aerial/1x9bp4l/00, 1vx5kzv/00..03): sky #8d978c..#adb6a6 (saturation 0.08-0.09), ground
# #5e6152..#7e846d. The biome values are what reaches the screen after vanilla's own rain and daylight
# (ClientLevel.getSkyColor: 75 % toward 0.6 x luminance; FogRenderer: red/green x0.5, blue x0.6 in rain), set by
# measured frames (report: colour table), not by eye.
COLOURS = {
    "sky_color": 0xD9F2D1,
    "fog_color": 0xFFFAD1,
    "grass_color": 0x9A9C84,
    "foliage_color": 0x8A8670,
    "water_color": 0x5B6157,
    "water_fog_color": 0x2E322C,
}
# Drifting fine dust (1x9bp4l lower right): vanilla dust particle in the frames' haze colour; probability per random
# display tick position (vanilla: basalt deltas white ash 0.118, soul sand valley ash 0.00625).
PARTICLE = {"options": {"type": "minecraft:dust", "color": [0.62, 0.60, 0.52], "scale": 1.5}, "probability": 0.012}


def twin_id(orig: str) -> str:
    ns, path = orig.split(":", 1)
    return f"{NS}:{PREFIX}{ns}/{path}"


def orig_id(twin: str) -> str | None:
    ns, path = twin.split(":", 1)
    if ns != NS or not path.startswith(PREFIX):
        return None
    rest = path[len(PREFIX):]
    if "/" not in rest:
        return None
    o_ns, o_path = rest.split("/", 1)
    return f"{o_ns}:{o_path}"


def twin(biome: dict, colours: dict = COLOURS, particle: dict = PARTICLE) -> dict:
    """The dead twin of one biome (datapack JSON): same climate, spawns, features and sounds; no precipitation."""
    t = json.loads(json.dumps(biome))
    t["has_precipitation"] = False
    eff = t.setdefault("effects", {})
    eff.update(colours)
    eff["grass_color_modifier"] = "none"   # swamp and dark forest would replace or darken the dead grass
    eff["particle"] = particle
    return t


FN_ON = """\
# The dead outside: overcast that stays, dead biomes near players (Almighty rule silo-outside).
execute unless data storage silo:outside {on:1b} store result storage silo:outside cycle byte 1 run gamerule doWeatherCycle
data modify storage silo:outside on set value 1b
gamerule doWeatherCycle false
weather rain
tellraw @s {"text":"Outside: dead world on (biomes change as players see them)","color":"gray"}
"""

FN_OFF = """\
# Back to the living world: clear weather, the weather cycle as it was before "on", biomes restored near players.
data modify storage silo:outside on set value 0b
weather clear
execute if data storage silo:outside {cycle:1b} run gamerule doWeatherCycle true
execute if data storage silo:outside {cycle:0b} run gamerule doWeatherCycle false
tellraw @s {"text":"Outside: living world restored (biomes change back as players see them)","color":"gray"}
"""

NOTE = """\
# Silo outside weather

The silo server can show the dead outside of the series' present day: overcast grey sky, flat light, dust in the
air, dead grass and leaves, no rain. Artem switches it; do not switch it on your own.

- `/function silo:outside/on`: overcast held (weather rain with the weather cycle off) and dead biomes
  (`silo:dead/<namespace>/<path>`) swapped in by the persisted Almighty rule `silo-outside` in the chunks players see.
- `/function silo:outside/off`: clear weather, the weather cycle as before, original biomes swapped back.
- State: command storage `silo:outside` (`on`, `cycle`). Do not remove the rule `silo-outside`: with "off" it puts
  back the biomes of chunks still dead. Do not change the weather while "on": rain is how the overcast is made.
"""


# Biome tags of every twin, and only these: overworld (Particle Rain spawns its dust only in #c:is_overworld biomes).
# Not a desert tag: Iris derives the shaders' biome_category from vanilla tags (BiomeUniforms, 1.8.14: desert pyramid
# -> DESERT), and Photon then draws its desert sandstorm in rain, which is orange (blue extinction 0.45 against red
# 0.2, colour 1.00/0.83/0.60) and dense: test copy 18.11, frames 12-17, against the series' grey haze with the
# skyline still visible. Without it the twins are temperate and Photon draws its own overcast.
TAGS = ("minecraft:is_overworld", "c:is_overworld")


def pack(dump: dict, out: str) -> int:
    """Write the datapack; returns the number of twins."""
    root = os.path.join(out, "data")
    n = 0
    for tag in TAGS:
        ns, path = tag.split(":", 1)
        f = os.path.join(root, ns, "tags", "worldgen", "biome", path + ".json")
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f, "w") as fh:
            json.dump({"replace": False, "values": [twin_id(o) for o in sorted(dump)]}, fh, indent=1)
    for orig, biome in sorted(dump.items()):
        ns, path = twin_id(orig).split(":", 1)
        f = os.path.join(root, ns, "worldgen", "biome", path + ".json")
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f, "w") as fh:
            json.dump(twin(biome), fh, indent=1, sort_keys=True)
        n += 1
    fn = os.path.join(root, NS, "function", "outside")
    os.makedirs(fn, exist_ok=True)
    open(os.path.join(fn, "on.mcfunction"), "w").write(FN_ON)
    open(os.path.join(fn, "off.mcfunction"), "w").write(FN_OFF)
    notes = os.path.join(root, NS, "almighty", "notes")
    os.makedirs(notes, exist_ok=True)
    open(os.path.join(notes, "outside.md"), "w").write(NOTE)
    with open(os.path.join(out, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"pack_format": 48, "description": "Silo: the dead outside (/function silo:outside/on|off)"}}, fh)
    return n


DUMP = r"""
import com.mojang.serialization.JsonOps
import net.minecraft.resources.RegistryOps
import net.minecraft.core.registries.Registries
import net.minecraft.world.level.biome.Biome
import net.minecraft.tags.BiomeTags
def reg = server.registryAccess().registryOrThrow(Registries.BIOME)
def ops = RegistryOps.create(JsonOps.INSTANCE, server.registryAccess())
def out = [:]
reg.holders().forEach { h ->
  def id = h.key().location()
  if (id.namespace == 'silo') return
  if (h.is(BiomeTags.IS_OVERWORLD) || id.namespace == 'incoming')
    out[id.toString()] = Biome.DIRECT_CODEC.encodeStart(ops, h.value()).getOrThrow().toString()
}
return out
"""

# The rule: every 10 server ticks, nearest-first over the chunks each player has been sent, swap biome cells above
# the chunk's lowest surface - 8 (forward while storage silo:outside on=1b, back otherwise). A chunk once brought to
# the current state is rechecked after RECHECK ticks (a new nuke may write Incoming tiers into it). Stops at MS per run.
RULE_CODE = r"""
import groovy.transform.CompileStatic
import net.minecraft.core.Holder
import net.minecraft.core.QuartPos
import net.minecraft.core.Registry
import net.minecraft.core.registries.Registries
import net.minecraft.resources.ResourceKey
import net.minecraft.resources.ResourceLocation
import net.minecraft.server.MinecraftServer
import net.minecraft.server.level.ChunkMap
import net.minecraft.server.level.ServerLevel
import net.minecraft.server.level.ServerPlayer
import net.minecraft.world.level.ChunkPos
import net.minecraft.world.level.biome.Biome
import net.minecraft.world.level.biome.BiomeResolver
import net.minecraft.world.level.biome.Climate
import net.minecraft.world.level.chunk.ChunkAccess
import net.minecraft.world.level.chunk.LevelChunk
import net.minecraft.world.level.chunk.LevelChunkSection
import net.minecraft.world.level.levelgen.Heightmap
import java.util.function.Consumer

// Statically compiled: dynamic Groovy spent 10-40 ms a run on call dispatch alone (test copy, 18.11).
@CompileStatic
class SiloOutside {
    static final double MS = 4.0d       // per run; the rule runs every 10 ticks
    static final int RECHECK = 600      // ticks before a chunk already in the current state is looked at again

    static void run(MinecraftServer server, Map<String, Object> state) {
        long t0 = System.nanoTime()
        ServerLevel lvl = server.overworld()
        List<ServerPlayer> players = lvl.players()
        if (players.isEmpty()) return
        boolean on = server.getCommandStorage().get(ResourceLocation.parse('silo:outside')).getBoolean('on')
        List<Map<Holder<Biome>, Holder<Biome>>> maps = (List<Map<Holder<Biome>, Holder<Biome>>>) state.get('silo.outside.maps')
        if (maps == null) {
            Map<Holder<Biome>, Holder<Biome>> fwd = new HashMap<>(), back = new HashMap<>()
            Registry<Biome> reg = server.registryAccess().registryOrThrow(Registries.BIOME)
            for (Holder.Reference<Biome> h : reg.holders().toList()) {
                ResourceLocation id = h.key().location()
                if (id.namespace != 'silo' || !id.path.startsWith('dead/')) continue
                String rest = id.path.substring(5)
                int i = rest.indexOf('/')
                def o = reg.getHolder(ResourceKey.create(Registries.BIOME, ResourceLocation.fromNamespaceAndPath(rest.substring(0, i), rest.substring(i + 1))))
                if (o.isPresent()) { fwd.put(o.get(), h); back.put(h, o.get()) }
            }
            maps = [fwd, back]
            state.put('silo.outside.maps', maps)
            state.put('silo.outside.seen', new HashMap<Long, long[]>())
            state.put('silo.outside.stats', [swapped: 0L, cells: 0L, scanned: 0L, runs: 0L, ms: 0.0d, maxMs: 0.0d] as Map<String, Object>)
        }
        Map<Holder<Biome>, Holder<Biome>> m = on ? maps[0] : maps[1]
        Map<Long, long[]> seen = (Map<Long, long[]>) state.get('silo.outside.seen')
        Map<String, Object> st = (Map<String, Object>) state.get('silo.outside.stats')
        long now = lvl.getGameTime()
        long mode = on ? 1L : 0L
        ChunkMap cm = lvl.getChunkSource().chunkMap
        int vd = server.getPlayerList().getViewDistance()
        int[][] offs = (int[][]) state.get('silo.outside.offs' + vd)
        if (offs == null) {
            List<int[]> l = []
            for (int dx = -vd; dx <= vd; dx++) for (int dz = -vd; dz <= vd; dz++) l.add([dx, dz, dx * dx + dz * dz] as int[])
            l.sort { int[] a, int[] b -> a[2] <=> b[2] }
            offs = l.toArray(new int[0][])
            state.put('silo.outside.offs' + vd, offs)
        }
        Climate.Sampler sampler = lvl.getChunkSource().randomState().sampler()
        List<ChunkAccess> resend = []
        long scanned = 0, swapped = 0, cells = 0
        boolean out = false
        for (ServerPlayer p : players) {
            if (out) break
            int pcx = p.chunkPosition().x, pcz = p.chunkPosition().z
            for (int[] o : offs) {
                if ((System.nanoTime() - t0) > (long) (MS * 1e6)) { out = true; break }
                int cx = pcx + o[0], cz = pcz + o[1]
                long key = ChunkPos.asLong(cx, cz)
                long[] s = seen.get(key)
                if (s != null && s[0] == mode && now - s[1] < RECHECK) continue
                LevelChunk chunk = lvl.getChunkSource().getChunkNow(cx, cz)
                if (chunk == null) continue
                if (cm.getPlayers(new ChunkPos(cx, cz), false).isEmpty()) continue   // not yet sent to anyone
                scanned++
                int low = Integer.MAX_VALUE
                for (int x = 0; x < 16; x += 3) for (int z = 0; z < 16; z += 3) low = Math.min(low, chunk.getHeight(Heightmap.Types.WORLD_SURFACE, x, z))
                for (int z = 0; z < 16; z += 3) low = Math.min(low, chunk.getHeight(Heightmap.Types.WORLD_SURFACE, 15, z))
                int y0 = low - 8
                int qyMin = QuartPos.fromBlock(y0)
                LevelChunkSection[] sections = chunk.getSections()
                int[] changed = [0] as int[]
                for (int i = Math.max(0, chunk.getSectionIndex(y0)); i < sections.length; i++) {
                    LevelChunkSection sec = sections[i]
                    boolean[] need = [false] as boolean[]
                    sec.getBiomes().getAll({ Holder<Biome> h -> if (m.containsKey(h)) need[0] = true } as Consumer<Holder<Biome>>)
                    if (!need[0]) continue
                    sec.fillBiomesFromNoise({ int x, int y, int z, Climate.Sampler smp ->
                        Holder<Biome> h = chunk.getNoiseBiome(x, y, z)
                        Holder<Biome> t = y >= qyMin ? m.get(h) : null
                        if (t != null) { changed[0]++; return t }
                        return h
                    } as BiomeResolver, sampler, QuartPos.fromSection(cx), QuartPos.fromSection(chunk.getSectionYFromSectionIndex(i)), QuartPos.fromSection(cz))
                }
                seen.put(key, [mode, now] as long[])
                if (changed[0] > 0) {
                    chunk.setUnsaved(true)
                    resend.add(chunk)
                    swapped++
                    cells += changed[0]
                }
            }
        }
        if (!resend.isEmpty()) cm.resendBiomesForChunks(resend)
        double ms = (System.nanoTime() - t0) / 1e6d
        st.put('scanned', ((Long) st.get('scanned')) + scanned)
        st.put('swapped', ((Long) st.get('swapped')) + swapped)
        st.put('cells', ((Long) st.get('cells')) + cells)
        st.put('runs', ((Long) st.get('runs')) + 1L)
        st.put('ms', ((Double) st.get('ms')) + ms)
        st.put('maxMs', Math.max((Double) st.get('maxMs'), ms))
    }
}
SiloOutside.run(server, (Map<String, Object>) state)
"""

STATUS = r"""
def st = state['silo.outside.stats']
def tag = server.getCommandStorage().get(net.minecraft.resources.ResourceLocation.parse('silo:outside'))
return [on: tag.getBoolean('on'), cycle: tag.contains('cycle') ? tag.getByte('cycle') : null,
        stats: st, seen: state['silo.outside.seen']?.size(), twins: state['silo.outside.maps']?.get(0)?.size(),
        raining: server.overworld().isRaining(), weatherCycle: server.overworld().getGameRules().getBoolean(net.minecraft.world.level.GameRules.RULE_WEATHER_CYCLE)]
"""

CENSUS = r"""
def lvl = server.overworld()
int cx0 = (args.x as int) >> 4, cz0 = (args.z as int) >> 4, r = args.r as int
def out = [:]
for (int cx = cx0 - r; cx <= cx0 + r; cx++) for (int cz = cz0 - r; cz <= cz0 + r; cz++) {
  def c = lvl.getChunkSource().getChunkNow(cx, cz)
  if (c == null) continue
  def hist = [:]
  // count, not getAll: getAll reports each distinct value once per section; Lithium's count also reports zeros
  for (sec in c.getSections()) sec.getBiomes().count({ h, int n ->
    if (n <= 0) return
    def k = h.unwrapKey().map { it.location().toString() }.orElse('?')
    hist[k] = (hist[k] ?: 0) + n } as net.minecraft.world.level.chunk.PalettedContainer.CountConsumer)
  out["${cx},${cz}"] = hist
}
return out
"""


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump"); d.add_argument("out")
    p = sub.add_parser("pack"); p.add_argument("dump"); p.add_argument("out")
    r = sub.add_parser("rule"); r.add_argument("action", choices=["install", "remove", "status"])
    c = sub.add_parser("census"); c.add_argument("x", type=int); c.add_argument("z", type=int); c.add_argument("r", type=int)
    a = ap.parse_args()
    if a.cmd == "pack":
        n = pack(json.load(open(a.dump)), a.out)
        print(f"{n} dead twins in {a.out}")
        return
    from build_live import Bridge
    br = Bridge()
    if a.cmd == "dump":
        res = br.call("script", {"code": DUMP, "timeout_ms": 10000})
        dump = {k: json.loads(v) for k, v in res["value"].items()}
        json.dump(dump, open(a.out, "w"), indent=1, sort_keys=True)
        print(f"{len(dump)} biomes -> {a.out}")
    elif a.cmd == "rule":
        if a.action == "install":
            try:
                br.call("rule.remove", {"name": RULE})
            except RuntimeError:
                pass
            print(br.call("rule.add", {"event": "tick", "name": RULE,
                                       "every": 10, "budget_ms": 2, "persist": True, "script": RULE_CODE}))
        elif a.action == "remove":
            print(br.call("rule.remove", {"name": RULE}))
        else:
            print(json.dumps(br.call("script", {"code": STATUS})["value"], indent=1))
            print(json.dumps([x for x in br.call("rules", {}) if (x.get("name") == RULE)], indent=1))
    elif a.cmd == "census":
        res = br.call("script", {"code": CENSUS, "args": {"x": a.x, "z": a.z, "r": a.r}, "timeout_ms": 10000})
        print(json.dumps(res["value"], sort_keys=True))
        print(f"census: {len(res['value'])} loaded chunks, {res.get('ms')} ms", file=sys.stderr)


if __name__ == "__main__":
    main()
