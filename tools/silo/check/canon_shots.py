"""Shots of Silo 18 matching the show's surface frames, poses from the layout (axis = dir): python3 gen_shots.py > canon.json"""
import json, math
L = json.load(open('' + __import__('sys').argv[1] + ''))
P = {s['number']: s['ring'] for s in L['silos']}
CARD = {"W": (-1, 0), "N": (0, -1), "E": (1, 0), "S": (0, 1)}
def yaw(dx, dz): return math.degrees(math.atan2(-dx, dz))
out = []
for n in (18, 7):
    s = next(s for s in L['silos'] if s['number'] == n)
    cx, cz = P[n]; ax, az = CARD[s['dir']]           # toward the slot
    at = lambda r, side=0: (cx + 0.5 + r * ax - side * az, cz + 0.5 + r * az + side * ax)
    x, z = at(-88)                                   # 05: drone over the cut-side berm, looking along the axis to the slot side
    out.append(dict(name=f'{n}-05-path-into-bowl', x=x, y=None, z=z, yaw=yaw(ax, az), pitch=22, fov=60, dy=16))
    x, z = at(34, 2)                                 # 07: beyond the slot's low end, looking back at the head and the block
    out.append(dict(name=f'{n}-07-camera-block', x=x, y=None, z=z, yaw=yaw(-ax, -az), pitch=4, fov=60))
    x, z = at(16, -1)                                # 10: from the bowl over the stair head to the berm on the slot side
    out.append(dict(name=f'{n}-10-stair-head-berm', x=x, y=None, z=z, yaw=yaw(ax, az), pitch=-2, fov=60, dy=1.2))
    x, z = at(25)                                    # 27: the slot from above
    out.append(dict(name=f'{n}-27-slot-top-down', x=x, y=None, z=z, yaw=yaw(ax, az), pitch=89, fov=50, dy=14))
    x, z = at(31, 6)                                 # 06: at the slot's rim, looking along it to the head
    out.append(dict(name=f'{n}-06-slot-rim', x=x, y=None, z=z, yaw=yaw(-ax, -az + 0.3), pitch=18, fov=60))
print(json.dumps(out, indent=0))
