"""Load every chunk of the 1:1 field once on the test server (so the game lights and re-saves what build_offline.py
wrote with isLightOn 0), tile by tile. uv run --with httpx --with numpy sweep.py x0 z0 x1 z1 [tile]
Progress in sweep.done (one tile per line), so a rerun goes on where it stopped."""
import os, sys, time
os.environ['ALMIGHTY_URL'] = 'http://10.0.6.2:25654'
os.environ['ALMIGHTY_TOKEN_FILE'] = '/home/ubuntu/airstrike-server/crafty/docker/servers/9441693a-aa56-4a93-8f01-4647e1131800/config/almighty/token'
sys.path.insert(0, os.path.expanduser('~/claude/silo-1to1/tools/silo'))
from build_live import Bridge, settle
br = Bridge()
x0, z0, x1, z1 = map(int, sys.argv[1:5]); T = int(sys.argv[5]) if len(sys.argv) > 5 else 160
done_f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweep.done')
done = set(open(done_f).read().split()) if os.path.exists(done_f) else set()
tiles = [(x, z) for x in range(x0, x1, T) for z in range(z0, z1, T)]
t0 = time.time()
for k, (x, z) in enumerate(tiles):
    key = f'{x},{z}'
    if key in done:
        continue
    a = br.call('area.prepare', {'from': [x, z], 'to': [x + T - 1, z + T - 1], 'ttl_seconds': 120, 'wait': 50})
    if a.get('ready', 0) < a.get('chunks', 1):
        print(f'tile {key}: only {a.get("ready")}/{a.get("chunks")} ready', flush=True)
        br.call('area.release', {'id': a['id']})
        continue
    br.call('area.release', {'id': a['id']})
    open(done_f, 'a').write(key + '\n')
    settle(br, limit=1000, log=lambda m: print(m, flush=True))
    st = br.call('status', {})
    if k % 10 == 0:
        print(f'{k + 1}/{len(tiles)} tiles, {time.time() - t0:.0f}s, tps {st["tps"]} mspt {st["mspt"]}', flush=True)
print('SWEEP DONE', len(tiles), f'{time.time() - t0:.0f}s', flush=True)
