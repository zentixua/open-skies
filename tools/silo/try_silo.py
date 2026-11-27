import sys, time
sys.path.insert(0, '.')
from silo import Silo, Spec
import preview
t = time.time()
s = Silo(Spec(), 0, 68, 0)
v = s.build()
print('built in %.1fs size %s palette %d' % (time.time() - t, v.size, len(v.palette)))
out = sys.argv[1]
preview.section_xy(v, s.R, f'{out}/sec_full.png')
L1 = s.level_y(1); preview.section_xy(v, s.R, f'{out}/sec_top.png', L1 - 40, L1 + 30, 4)
preview.slice_y(v, s.level_y(30) + 1, f'{out}/slice_l30.png')
preview.slice_y(v, s.level_y(1) + 1, f'{out}/slice_l1.png')
preview.slice_y(v, s.yi(s.gen_floor_rel) + 2, f'{out}/slice_gen.png')
print('L1', L1, 'grade', s.yi(0), 'height', v.size[1], 'world bottom', s.origin[1])
