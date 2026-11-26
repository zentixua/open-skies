"""mcfunction for the gallery airship: Create Aeronautics blocks, long axis along Z (bow toward -Z), envelope centre (cx, cy, cz).

python3 airship.py 105 132 -652 > airship.mcfunction   (then /function, which also assembles it)"""
import sys
cx, cy, cz = map(int, sys.argv[1:4])
a, b, c = 13.0, 5.2, 5.2   # semi-axes: Z (length), Y, X
cmds = []
def sb(x, y, z, block): cmds.append(f"setblock {x} {y} {z} {block}")
# envelope shell, orange band on the equator
for dz in range(-14, 15):
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            d = (dz/a)**2 + (dy/b)**2 + (dx/c)**2
            if d > 1: continue
            # shell: a neighbour outside the ellipsoid
            out = any(((dz+ez)/a)**2 + ((dy+ey)/b)**2 + ((dx+ex)/c)**2 > 1
                      for ex, ey, ez in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)))
            if not out:
                cmds.append(f"setblock {cx+dx} {cy+dy} {cz+dz} aeronautics:levitite")
                continue
            blk = "aeronautics:orange_envelope" if dy == 0 else "aeronautics:white_envelope"
            sb(cx+dx, cy+dy, cz+dz, blk)
# tail fins at the stern (+Z): a cross of thin fins, white with orange edges, tapering aft
import math
for dz in range(9, 16):
    r = b * math.sqrt(max(0.0, 1 - (dz/a)**2))          # envelope radius at this station
    tip = int(round(max(r, 0) + 2.5 - max(0, dz - 13)))   # fin edge, shrinking past the tail
    for k in range(int(r) + 1, tip + 1):
        edge = "aeronautics:orange_envelope" if k == tip else "aeronautics:white_envelope"
        sb(cx, cy + k, cz + dz, edge); sb(cx, cy - k, cz + dz, edge)
        sb(cx + k, cy, cz + dz, edge); sb(cx - k, cy, cz + dz, edge)
    if r < 1:
        sb(cx, cy, cz + dz, "aeronautics:white_envelope")
# gondola: spruce hull under the envelope
gy = cy - 9
for dz in range(-6, 7):
    w = 2 if abs(dz) < 5 else 1
    for dx in range(-w, w + 1):
        sb(cx+dx, gy, cz+dz, "minecraft:spruce_planks")
        if abs(dx) == w or abs(dz) == 6:
            sb(cx+dx, gy+1, cz+dz, "minecraft:spruce_planks")
    sb(cx-w-0, gy-1, cz+dz, "minecraft:spruce_slab[type=top]") if abs(dz) < 6 else None
    for dx in range(-w + 1, w):
        sb(cx+dx, gy-1, cz+dz, "minecraft:dark_oak_planks") if abs(dz) < 6 else None
# keel line and windows (glass panes in the hull side)
for dz in (-3, 0, 3):
    sb(cx-2, gy+1, cz+dz, "minecraft:glass")
    sb(cx+2, gy+1, cz+dz, "minecraft:glass")
# rigging posts from the gondola up to the envelope
for dx in (-2, 2):
    for dz in (-4, 4):
        for y in range(gy + 2, cy - 4):
            sb(cx+dx, y, cz+dz, "minecraft:dark_oak_fence")
# burner under the envelope (hot air), lanterns, wheel
sb(cx, gy + 1, cz, "aeronautics:adjustable_burner[powered=true]")
for y in range(gy + 2, cy - 4): sb(cx, y, cz, "aeronautics:white_envelope_encased_shaft[axis=y]")
sb(cx, gy + 1, cz - 4, "simulated:steering_wheel[facing=north,on_floor=true]")
for dz in (-5, 5):
    sb(cx, gy + 2, cz+dz, "minecraft:lantern")
# propeller at the stern of the gondola, blowing aft
sb(cx, gy, cz + 7, "aeronautics:propeller_bearing[facing=south]")
sb(cx, gy, cz + 8, "aeronautics:wooden_propeller[facing=south]")
# levitite keeps it afloat (Create Aeronautics' floating block), hidden inside the envelope
for dz in (-6, -3, 0, 3, 6):
    sb(cx, cy, cz + dz, "aeronautics:levitite")
cmds.append(f"sable assemble area {cx-9} {gy-2} {cz-16} {cx+9} {cy+9} {cz+16}")
print("\n".join(cmds))
