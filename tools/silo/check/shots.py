"""uv run --with httpx --with numpy shots.py <shots.json> <outdir>: see-renders on the 1to1 test server.
shots.json: [{"name", "x", "y" (eye y, or null = ground + 1.62), "z", "yaw", "pitch", "fov"?}]"""
import base64, json, math, os, sys
os.environ['ALMIGHTY_URL'] = 'http://10.0.6.2:25654'
os.environ['ALMIGHTY_TOKEN_FILE'] = '/home/ubuntu/airstrike-server/crafty/docker/servers/9441693a-aa56-4a93-8f01-4647e1131800/config/almighty/token'
sys.path.insert(0, os.path.expanduser('~/claude/silo-1to1/tools/silo'))
from build_live import Bridge
br = Bridge()
shots = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
H = "import net.minecraft.world.level.levelgen.Heightmap\nserver.overworld().getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, args.x as int, args.z as int)"
for s in shots:
    x, z = s['x'], s['z']
    a = br.call('area.prepare', {'from': [int(x) - 96, int(z) - 96], 'to': [int(x) + 96, int(z) + 96], 'ttl_seconds': 300, 'wait': 50})
    try:
        y = s.get('y')
        if y is None:
            y = br.call('script', {'code': H, 'args': {'x': math.floor(x), 'z': math.floor(z)}})['value'] + 1.62
        r = br.call('see', {'at': [x, y, z], 'yaw': s['yaw'], 'pitch': s['pitch'], 'image': True, 'width': 480, 'height': 270,
                            'fov': s.get('fov', 70), 'wait': 50})
        while r.get('state') not in (None, 'done'):
            r = br.call('job', {'id': r['id'], 'wait': 50})
        open(f"{out}/{s['name']}.png", 'wb').write(base64.b64decode(r['png_base64']))
        print(s['name'], 'eye', round(y, 1), flush=True)
    finally:
        br.call('area.release', {'id': a['id']})
