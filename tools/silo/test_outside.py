"""python3 -m unittest tools/silo/test_outside.py: dead twins and the twin <-> original mapping."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outside  # noqa: E402

PLAINS = {"has_precipitation": True, "temperature": 0.8, "downfall": 0.4,
          "effects": {"sky_color": 7907327, "fog_color": 12638463, "water_color": 4159204, "water_fog_color": 329011,
                      "mood_sound": {"sound": "minecraft:ambient.cave"}},
          "spawners": {"creature": [{"type": "minecraft:cow", "weight": 8, "minCount": 4, "maxCount": 4}]},
          "spawn_costs": {}, "carvers": [], "features": [["minecraft:lake_lava_underground"]]}
SWAMP = {**PLAINS, "effects": {**PLAINS["effects"], "grass_color_modifier": "swamp"}}


class Twins(unittest.TestCase):
    def test_ids_round_trip(self):
        for o in ("minecraft:plains", "incoming:charred", "terralith:a/b"):
            self.assertEqual(outside.orig_id(outside.twin_id(o)), o)
        self.assertIsNone(outside.orig_id("minecraft:plains"))
        self.assertIsNone(outside.orig_id("silo:other"))

    def test_twin_changes_only_look_and_rain(self):
        t = outside.twin(PLAINS)
        self.assertFalse(t["has_precipitation"])
        for k in ("temperature", "downfall", "spawners", "spawn_costs", "carvers", "features"):
            self.assertEqual(t[k], PLAINS[k], k)
        self.assertEqual(t["effects"]["mood_sound"], PLAINS["effects"]["mood_sound"])
        for k, v in outside.COLOURS.items():
            self.assertEqual(t["effects"][k], v)
        self.assertEqual(t["effects"]["particle"], outside.PARTICLE)
        self.assertTrue(PLAINS["has_precipitation"], "source untouched")

    def test_swamp_modifier_does_not_override_dead_grass(self):
        self.assertEqual(outside.twin(SWAMP)["effects"]["grass_color_modifier"], "none")

    def test_pack_layout(self):
        with tempfile.TemporaryDirectory() as d:
            n = outside.pack({"minecraft:plains": PLAINS, "incoming:singed": PLAINS}, d)
            self.assertEqual(n, 2)
            for p in ("data/silo/worldgen/biome/dead/minecraft/plains.json", "data/silo/worldgen/biome/dead/incoming/singed.json",
                      "data/silo/function/outside/on.mcfunction", "data/silo/function/outside/off.mcfunction",
                      "data/silo/almighty/notes/outside.md", "pack.mcmeta"):
                self.assertTrue(os.path.exists(os.path.join(d, p)), p)
            self.assertFalse(json.load(open(os.path.join(d, "data/silo/worldgen/biome/dead/minecraft/plains.json")))["has_precipitation"])
            self.assertFalse(os.path.exists(os.path.join(d, "data/minecraft/tags/worldgen/biome/has_structure")),
                             "no desert tag: Photon's desert sandstorm is orange (test copy 18.11)")
            for tag in ("minecraft/tags/worldgen/biome/is_overworld.json", "c/tags/worldgen/biome/is_overworld.json"):
                t = json.load(open(os.path.join(d, "data", tag)))
                self.assertFalse(t["replace"], tag)
                self.assertEqual(sorted(t["values"]), ["silo:dead/incoming/singed", "silo:dead/minecraft/plains"], tag)

    def test_off_restores_the_weather_cycle_saved_by_on(self):
        self.assertIn("unless data storage silo:outside {on:1b} store result storage silo:outside cycle", outside.FN_ON)
        self.assertIn("{cycle:1b} run gamerule doWeatherCycle true", outside.FN_OFF)
        self.assertIn("{cycle:0b} run gamerule doWeatherCycle false", outside.FN_OFF)


if __name__ == "__main__":
    unittest.main()
