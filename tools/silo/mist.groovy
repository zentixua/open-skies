// silo-mist (15.11, v7): white mist (nanites) low over the floor of each silo's airlock and the stair's foot,
// only where a player is within 24 blocks of that silo's vault door. Silo frame: way in due west, the vault door
// at x -33, the airlock x -32..-29 inward of it, the tunnel's inside z -2..1, its stair rising a block a step
// westward from x -35 (silo.py).
def S = [[3248,-2800,0,52],[2702,-3230,0,52],[2705,-3731,2,53],[2603,-3466,0,52],[2435,-3250,1,52],[2236,-3059,3,52],[2617,-2608,2,52],[2606,-2338,1,53],[2845,-2464,1,53],[2856,-2733,3,52],[2628,-2878,3,52],[2389,-2752,2,52],[2378,-2482,1,53],[3365,-2133,1,52],[3509,-1905,1,52],[3761,-1899,0,52],[3635,-2144,0,52],[3490,-2372,3,53],[3220,-2361,2,53],[3095,-2122,1,53],[3239,-1894,1,53],[2614,-1816,1,54],[2756,-1587,0,53],[2884,-1824,0,53],[2742,-2054,0,53],[2472,-2046,2,53],[2344,-1808,2,54],[2486,-1579,1,54],[3262,-3494,0,52],[3196,-3233,2,52],[3455,-3306,1,52],[3521,-3568,3,52],[3328,-3756,0,52],[3068,-3682,2,52],[3002,-3421,2,52],[4001,-3718,0,53],[4065,-3455,0,53],[4260,-3642,1,53],[4195,-3905,3,53],[3936,-3980,2,53],[3741,-3792,2,53],[3806,-3531,2,53],[3903,-2875,2,53],[3967,-2613,1,53],[4221,-2543,0,53],[4162,-2800,0,53],[4098,-3062,3,53],[3838,-3138,3,53],[3643,-2951,2,53],[3708,-2688,1,53]]
def lvl = server.overworld()
def ps = lvl.players()
if (ps.isEmpty()) return
def rnd = java.util.concurrent.ThreadLocalRandom.current()
for (s in S) {
  double vx = -32.5, vz = 0.0
  for (int t = 0; t < s[2]; t++) { double q = vx; vx = 1 - vz; vz = q }
  vx += s[0]; vz += s[1]
  boolean near = false
  for (p in ps) { if (p.distanceToSqr(vx, s[3] + 1.0, vz) < 576) { near = true; break } }
  if (!near) continue
  for (int i = 0; i < 10; i++) {
    double fx = -38 + rnd.nextDouble() * 10, fz = -2 + rnd.nextDouble() * 4
    double fy = s[3] + (fx < -34 ? -34 - Math.floor(fx) : 0) + 0.1 + rnd.nextDouble() * 0.5
    double x = fx, z = fz
    for (int t = 0; t < s[2]; t++) { double q = x; x = 1 - z; z = q }
    lvl.sendParticles(net.minecraft.core.particles.ParticleTypes.WHITE_SMOKE, s[0] + x, fy, s[1] + z, 2, 0.4, 0.03, 0.4, 0.0)
  }
}
