"""Check that every block state a volume uses exists in vanilla Minecraft 1.21.1.

blocks.json comes from the vanilla 1.21.1 server's data generator:
  java -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --reports --output gen   (gen/reports/blocks.json)
A copy is in /mnt/project-files/silo/vanilla-1.21.1-blocks.json. A state passes when the block exists, every given
property exists with a legal value (omitted properties take the block's default, as /setblock does).
"""
from __future__ import annotations

import json
import sys

DEFAULT_REPORT = "/mnt/project-files/silo/vanilla-1.21.1-blocks.json"


def load(path: str = DEFAULT_REPORT) -> dict:
    with open(path) as f:
        return json.load(f)


def problem(state: str, blocks: dict) -> str | None:
    if state == "<keep>":
        return None
    name, _, props = state.partition("[")
    if ":" not in name:
        name = "minecraft:" + name
    block = blocks.get(name)
    if block is None:
        return "no such block"
    legal = block.get("properties", {})
    if props:
        for kv in props.rstrip("]").split(","):
            k, _, val = kv.partition("=")
            if k not in legal:
                return f"no property {k}"
            if val not in legal[k]:
                return f"{k}={val} not in {legal[k]}"
    return None


def check(states, path: str = DEFAULT_REPORT) -> list[tuple[str, str]]:
    blocks = load(path)
    return [(s, p) for s in states if (p := problem(s, blocks))]


if __name__ == "__main__":
    sys.path.insert(0, ".")
    from silo import Silo, Spec
    from silo1 import Silo1
    bad = 0
    for label, silo in (("silo 18", Silo(Spec(number=18), 0, 70, 0)), ("silo 1", Silo1())):
        vol = silo.build()
        states = vol.used_states()
        errors = check(states)
        print(f"{label}: {len(states)} states, {len(errors)} not vanilla 1.21.1")
        for s, p in errors:
            print("   ", s, "-", p)
        bad += len(errors)
    sys.exit(1 if bad else 0)
