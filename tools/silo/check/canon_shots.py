"""Shots matching the show's surface frames (S3E09 05, 06, 07, 10; S3E10 27) on a silo's own axis: python3 canon_shots.py LAYOUT.json > shots.json"""
import json, math
import sys
L = json.load(open(sys.argv[1]))
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
    x, z = at(43, 2)                                 # 07: beyond the open head, looking back down the trench at the shelter
    out.append(dict(name=f'{n}-07-camera-block', x=x, y=None, z=z, yaw=yaw(-ax, -az), pitch=4, fov=60))
    x, z = at(35.5, 0)                               # 10: on the low steps, looking up past the head to the berm
    out.append(dict(name=f'{n}-10-stair-head-berm', x=x, y=None, z=z, yaw=yaw(ax, az), pitch=8, fov=60, dy=-4.0))
    x, z = at(37.5)                                  # 27: the trench from above
    out.append(dict(name=f'{n}-27-slot-top-down', x=x, y=None, z=z, yaw=yaw(ax, az), pitch=89, fov=50, dy=14))
    x, z = at(38, 5)                                 # 06: at the trench's rim, looking along it to the closed end
    out.append(dict(name=f'{n}-06-slot-rim', x=x, y=None, z=z, yaw=yaw(-ax, -az + 0.3), pitch=18, fov=60))
print(json.dumps(out, indent=0))
