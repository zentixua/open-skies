"""The generator hall, the digger void and the tunnel under a silo, from the explorethesilo.com model.

Source: silo3d.js buildGeneratorRoom, buildControlRoom (CTRL), buildDiggerVoid, buildTunnelEnd (explorethesilo.com,
taken apart for private use with Artem's permission). Bearings: silo = model + FRAME_DEG (bays.py).

The generator hall is the model's at 1:1: its wall is the shaft wall extended down (r 30.5), the machine stands at
r 16 on model bearing 120, its control room on bearing -3, fans on 120 and 280, lagged risers along the wall. Heights
are rows above the hall floor (row k holds model heights k..k+1 m). The digger void is the model's scaled into the
silo's void (radius void_radius for the model's 100 m, height void_height for its 90 m): cavern, machine, ring and
floor trusses scale; things a person uses (George's camp, ladders, lamps, the tunnel's 9.2 x 7.2 m bore and its
door) stay 1:1. The tunnel runs 68 m from the cavern on model bearing 52; the part beyond the silo's volume is a
separate Volume, Silo.tunnel_volume().
"""
from __future__ import annotations

import math

import numpy as np

from bays import FRAME_DEG
from volume import Volume

TAU = 2 * math.pi
AIR = "minecraft:air"
CONCRETE = "minecraft:light_gray_concrete"
CONCRETE_DARK = "minecraft:gray_concrete"
PILASTER = "minecraft:polished_andesite"
FLOOR = "minecraft:polished_deepslate"
RUST = "minecraft:waxed_weathered_copper"             # matRustSteel / matVesselSteel
RUST_CUT = "minecraft:waxed_weathered_cut_copper"
GRATE = "minecraft:waxed_weathered_copper_grate"      # matGrating
RED_RAIL = "minecraft:red_nether_brick_wall"          # matRedRail
POST = "minecraft:iron_bars"
ROCK = "minecraft:deepslate"
ROCK_DARK = "minecraft:deepslate_tiles"
WATER = "minecraft:water"
GLOW = "minecraft:shroomlight"                        # the chamber's orange glow, the fans' glow
HANG = "minecraft:lantern[hanging=true,waterlogged=false]"
LANTERN = "minecraft:lantern[hanging=false,waterlogged=false]"

WALL_R = 30.5                     # model SHAFT_RADIUS + 0.5
MACHINE_R, MACHINE_DEG, MACHINE_ROT = 16.0, 120.0, 40.5
CTRL = dict(deg=-3.0, floor=4.35, back=-2.85, front=2.6, half=4.6, win_x0=-3.4, win_x1=1.8, win_y0=5.05, win_y1=8.15, deck_z=4.6)
TUN_PHI, TUN_HW, TUN_H, TUN_LEN = 52.0, 4.6, 7.2, 68.0


def bearing(model_deg: float) -> float:
    """Silo-frame bearing (radians) of a model bearing (degrees)."""
    return math.radians(model_deg + FRAME_DEG)


def rows(h0: float, h1: float) -> range:
    """Rows above a floor holding model heights h0..h1 (row k holds k..k+1)."""
    k0, k1 = math.floor(h0 + 0.5), math.floor(h1 - 0.5)
    return range(k0, max(k0, k1) + 1)


class Builder:
    def __init__(self, silo):
        self.silo, self.s, self.v = silo, silo.s, silo.v
        self.X, self.Z = silo.X.astype(float), silo.Z.astype(float)

    # local frames ---------------------------------------------------------------------------------------------
    def frame(self, cx: float, cz: float, rot: float):
        """Distance and angle (radians, the frame's own) of every column from a centre (silo coordinates)."""
        dx, dz = self.X - cx, self.Z - cz
        return np.hypot(dx, dz), np.mod(np.arctan2(dz, dx) - rot, TAU)

    def put(self, x: float, y: int, z: float, state: str) -> None:
        self.v.set(self.silo.R + int(round(x)), y, self.silo.R + int(round(z)), state)

    def get(self, x: float, y: int, z: float) -> str:
        return self.v.get(self.silo.R + int(round(x)), y, self.silo.R + int(round(z)))

    def beam(self, p0, p1, half: float, state: str, step: float = 0.4) -> None:
        """A straight member of square section 2*half between two points (x, y, z) in silo coordinates."""
        n = max(1, int(math.dist(p0, p1) / step))
        h = max(0, int(round(half - 0.01)))
        for i in range(n + 1):
            t = i / n
            x, y, z = (p0[k] + (p1[k] - p0[k]) * t for k in range(3))
            xi, yi, zi = self.silo.R + int(round(x)), int(round(y)), self.silo.R + int(round(z))
            self.v.box(xi - h, yi - h, zi - h, xi + h, yi + h, zi + h, state)

    # generator hall -------------------------------------------------------------------------------------------
    def generator_hall(self) -> None:
        silo, s, v = self.silo, self.s, self.v
        yf = silo.yi(silo.gen_floor_rel)
        top = silo.yi(silo.y144_rel) - 2                     # last clear row under level 144's floor
        r = silo.r
        v.mask(yf - 1, yf - 1, r < s.r_inner_wall, FLOOR)
        v.mask(yf, top, silo.ring(WALL_R, s.r_inner_wall), CONCRETE)
        self.liner(yf, top)
        self.fans(yf)
        self.pipes(yf)
        self.machine(yf)
        self.control_room(yf)
        self.hatch(yf)

    def liner(self, yf: int, top: int) -> None:
        """Forty bays round the hall in two tiers (0 and 10 m): lower and upper panels with a seam, a pilaster, a base
        and a cornice. Left out where the control room (lower tier) and the fans stand."""
        silo, v = self.silo, self.v
        face = silo.ring(WALL_R, WALL_R + 1.0)
        th = np.mod(silo.theta - math.radians(FRAME_DEG), TAU)            # model bearing of each column
        k = np.floor(th / (TAU / 40))
        lateral = (th - (k + 0.5) * TAU / 40) * WALL_R                   # metres across the bay from its centre
        pil = face & (np.abs(lateral - 2.3) < 0.6)
        skip_ctrl = np.abs(((th - math.radians(CTRL["deg"]) + math.pi) % TAU) - math.pi) < math.radians(7)
        skip_fan = np.zeros_like(face)
        for a in (120, 280):
            skip_fan |= np.abs(((th - math.radians(a) + math.pi) % TAU) - math.pi) < math.radians(7)
        for tier in (0, 10):
            m = face & ~skip_fan & ~(skip_ctrl if tier == 0 else False)
            for dy, state in ((0, CONCRETE_DARK), (1, CONCRETE), (2, CONCRETE), (3, CONCRETE), (4, CONCRETE_DARK),
                              (5, CONCRETE), (6, CONCRETE), (7, CONCRETE), (8, CONCRETE), (9, PILASTER)):
                y = yf + tier + dy
                if y <= top:
                    v.mask(y, y, m, state)
                    v.mask(y, y, m & pil, PILASTER)

    def fans(self, yf: int) -> None:
        """Two wall fans (model 120 and 280 degrees): a ring grille 2 m in radius, its centre 4.8 m up, the glow of
        the fan behind it."""
        silo, v = self.silo, self.v
        for a in (120, 280):
            b = bearing(a)
            d = np.abs(((silo.theta - b + math.pi) % TAU) - math.pi) * WALL_R
            for dy in range(0, 8):
                rr = np.hypot(d, dy + 0.5 - 4.8)
                v.mask(yf + dy, yf + dy, silo.ring(WALL_R, WALL_R + 1) & (rr < 2.2), POST)
                v.mask(yf + dy, yf + dy, silo.ring(WALL_R + 1, WALL_R + 2) & (rr < 2.2), GLOW)

    def pipes(self, yf: int) -> None:
        """The pipe row: lagged risers 1.5 m thick and 8.6 m tall at r 28.3, flanged at 0.4, 3.4 and 6.4 m, each
        turning into the wall at the top."""
        for a in (104, 111, 150, 157, 166, 174, 183):
            b = bearing(a)
            px, pz = 28.3 * math.cos(b), 28.3 * math.sin(b)
            dist = np.hypot(self.X - px, self.Z - pz)
            m = dist < 0.95
            for dy in range(0, 9):
                self.v.mask(yf + dy, yf + dy, m, RUST_CUT if dy in (0, 3, 6) else RUST)
            for rr in np.arange(28.3, WALL_R + 0.6, 0.5):
                self.put(rr * math.cos(b), yf + 8, rr * math.sin(b), RUST)

    def machine(self, yf: int) -> None:
        """The turbine vessel on its plinth, the walkway and stair to its hatch, the ring catwalk on six columns,
        ladders to the cap deck, work lamps. Machine-local bearings turn by the machine's 40.5 degrees."""
        silo, v = self.silo, self.v
        b = bearing(MACHINE_DEG)
        mx, mz = MACHINE_R * math.cos(b), MACHINE_R * math.sin(b)
        rot = math.radians(-MACHINE_ROT + FRAME_DEG)          # local angle a sits at silo bearing a + rot
        dist, ang = self.frame(mx, mz, rot)

        def ring(r0, r1):
            return (dist >= r0) & (dist < r1)

        def at(r, a_deg):
            a = math.radians(a_deg) + rot
            return mx + r * math.cos(a), mz + r * math.sin(a)

        v.mask(yf, yf, dist < 10.6, CONCRETE)                         # plinth r 11 -> 9, 1.2 m
        for dy in rows(1.2, 4.2):                                      # flared skirt r 8.5 -> 4.2 over 3 m
            rr = 8.5 - (dy + 0.5 - 1.2) / 3.0 * 4.3
            v.mask(yf + dy, yf + dy, dist < rr, RUST)
        for dy in range(4, 13):                                        # vessel r 4.4 to 13.2 m
            v.mask(yf + dy, yf + dy, dist < 4.4, RUST)
            v.mask(yf + dy, yf + dy, dist < 3.7, AIR)                  # hollow: a pressure vessel
        for h in (4.8, 8.7, 12.6):                                     # bands
            v.mask(yf + int(h), yf + int(h), ring(3.7, 4.9), RUST_CUT)
        gap = (ang >= math.radians(348)) | (ang < math.radians(48))    # the 60 degrees of lifted panels
        for dy in (7, 8, 9):                                           # mid band 7.0-9.85: chamber glowing inside
            v.mask(yf + dy, yf + dy, ring(3.7, 4.4) & ~gap, GLOW)
            v.mask(yf + dy, yf + dy, ring(3.7, 4.9) & gap, AIR)
            v.mask(yf + dy, yf + dy, dist < 0.9, "minecraft:iron_block")   # the rotor's shaft
        for k in range(10):                                            # rotor blades 2.6 m
            a = k * 36
            for rr in (1.4, 2.4):
                x, z = at(rr, a)
                self.put(x, yf + 8, z, POST)
        for k in range(2):                                             # the two lifted panels stand on the floor
            x, z = at(7.2, k * 30)
            self.put(x, yf + 1, z, RUST_CUT)
            self.put(x, yf + 2, z, RUST_CUT)
        v.mask(yf + 13, yf + 13, dist < 4.9, RUST)                     # cap flare
        v.mask(yf + 13, yf + 13, ring(4.9, 6.2), GRATE)                # cap deck at 14.5
        v.mask(yf + 14, yf + 14, ring(5.7, 6.2), RED_RAIL)
        # the hatch with its wheel at 15 degrees, 5.4 m up, and the walkway to it
        hx, hz = at(4.4, 15)
        f = silo.facing_radial(math.radians(15) + rot)
        for dy, half in ((4, "lower"), (5, "upper")):
            self.put(hx, yf + dy, hz, f"minecraft:iron_door[facing={f},half={half},hinge=left,open=false,powered=false]")
        wa = math.radians(15) + rot
        ca, sa = math.cos(wa), math.sin(wa)
        lat = (self.X - mx) * -sa + (self.Z - mz) * ca
        alo = (self.X - mx) * ca + (self.Z - mz) * sa
        deck = (np.abs(lat) < 1.3) & (alo >= 4.6) & (alo < 16.0)
        v.mask(yf + 3, yf + 3, deck & (dist >= 4.4), GRATE)            # deck at 4.15 m
        rail = (np.abs(lat) >= 1.3) & (np.abs(lat) < 2.2) & (alo >= 4.9) & (alo < 16.0)
        v.mask(yf + 4, yf + 4, rail & (dist >= 4.9), RED_RAIL)
        up = silo.facing_radial(wa + math.pi)                          # stairs climb toward the vessel
        for i, dy in enumerate((2, 1, 0)):                             # 22 risers down to the floor
            m = (np.abs(lat) < 1.3) & (alo >= 16.0 + i * 2.05) & (alo < 16.0 + (i + 1) * 2.05)
            v.mask(yf + dy, yf + dy, m, f"minecraft:polished_deepslate_stairs[facing={up},half=bottom,shape=straight,waterlogged=false]")
            for ddy in range(0, dy):
                v.mask(yf + ddy, yf + ddy, m, RUST)
            mr = (np.abs(lat) >= 1.3) & (np.abs(lat) < 2.2) & (alo >= 16.0 + i * 2.05) & (alo < 16.0 + (i + 1) * 2.05)
            v.mask(yf + dy + 1, yf + dy + 1, mr, RED_RAIL)
        for x in (7.6, 12.0, 15.6):                                    # posts under the deck
            for sd in (-1, 1):
                px, pz = mx + x * ca - sd * 1.15 * sa, mz + x * sa + sd * 1.15 * ca
                for dy in range(0, 3):
                    if self.get(px, yf + dy, pz) == AIR:
                        self.put(px, yf + dy, pz, POST)
        # the ring catwalk at 7.2 m, r 9.2-11.4, on six columns at r 10.3, with a red rail at 11.3
        v.mask(yf + 6, yf + 6, ring(9.2, 11.4), GRATE)
        v.mask(yf + 7, yf + 7, ring(10.9, 11.6), RED_RAIL)
        for k in range(6):
            x, z = at(10.3, 45 + 60 * k)
            for dy in range(0, 6):
                self.put(x, yf + dy, z, CONCRETE)
        for a in (100, 250):                                           # ladders up the vessel, catwalk to cap deck
            la = math.radians(a) + rot
            lx, lz = mx + 4.9 * math.cos(la), mz + 4.9 * math.sin(la)
            f = silo.facing_radial(la)
            dx, dz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[f]
            for dy in range(7, 14):
                self.put(lx - dx, yf + dy, lz - dz, RUST)
                self.put(lx, yf + dy, lz, f"minecraft:ladder[facing={f},waterlogged=false]")
        for x, z, kind in ((-10, 5, "stand"), (-11, -5, "stand"), (13, -4, "stand"), (3, -14, "stand"),
                           (-4, 10.8, "rail"), (9, -6.8, "rail")):
            a = math.atan2(z, x) + rot                                 # machine-local (x, z) to silo
            rr = math.hypot(x, z)
            px, pz = mx + rr * math.cos(a), mz + rr * math.sin(a)
            if kind == "stand":                                        # a 2.4 m lamp stand
                self.put(px, yf, pz, POST)
                self.put(px, yf + 1, pz, POST)
                self.put(px, yf + 2, pz, LANTERN)
            else:                                                      # on the catwalk rail
                self.put(px, yf + 8, pz, LANTERN)

    def control_room(self, yf: int) -> None:
        """The control room in the wall on model bearing -3: a box 9.2 m wide from 2.85 m behind the wall face to
        2.6 m in front of it, floor 4.35 m up, a long window, a door at its right end, a gallery deck along its front
        and a stair down at the left."""
        silo, v, C = self.silo, self.v, CTRL
        b = math.radians(C["deg"] + FRAME_DEG)
        er = np.array([math.cos(b), math.sin(b)])
        t = np.array([-math.sin(b), math.cos(b)])
        x = self.X * t[0] + self.Z * t[1]                      # across, metres
        zl = 30.0 - (self.X * er[0] + self.Z * er[1])          # inward from the model's wall (r 30)
        floor_dy = 3                                           # 4.35 m: walking surface at row 4
        body = (np.abs(x) < C["half"]) & (zl >= C["back"] - 0.3) & (zl < C["front"])
        inside = (np.abs(x) < C["half"] - 0.6) & (zl >= C["back"]) & (zl < C["front"] - 0.5)
        v.mask(yf, yf + 10, body, CONCRETE)
        v.mask(yf + floor_dy + 1, yf + 8, inside, AIR)
        v.mask(yf + floor_dy, yf + floor_dy, inside, FLOOR)
        front = body & (zl >= C["front"] - 0.5)
        win = front & (x >= C["win_x0"]) & (x < C["win_x1"])
        for dy in rows(C["win_y0"], C["win_y1"]):
            v.mask(yf + dy, yf + dy, win, "minecraft:glass_pane")
        door = front & (x >= 2.6) & (x < 3.7)
        fdir = silo.facing_radial(b + math.pi)
        dxz = np.argwhere(door)
        for i, k in dxz[:1]:
            for dy, half in ((floor_dy + 1, "lower"), (floor_dy + 2, "upper")):
                v.set(int(i), yf + dy, int(k), f"minecraft:iron_door[facing={fdir},half={half},hinge=left,open=false,powered=false]")
        lamp = inside & (np.abs(x) < 0.6) & (np.abs(zl) < 0.6)
        v.mask(yf + 9, yf + 9, lamp, "minecraft:sea_lantern")
        # the gallery deck: in front of the box from x -8.5 to the box's right end, and beside it back to z 0.5
        gal = ((x >= -8.5) & (x < C["half"]) & (zl >= C["front"]) & (zl < C["deck_z"])) | \
              ((x >= -8.5) & (x < -C["half"]) & (zl >= 0.5) & (zl < C["front"]))
        v.mask(yf + floor_dy, yf + floor_dy, gal, GRATE)
        rail = gal & ((zl >= C["deck_z"] - 0.9) | (x >= C["half"] - 0.9) | ((x < -7.6) & (zl >= 2.1)))
        v.mask(yf + floor_dy + 1, yf + floor_dy + 1, rail, RED_RAIL)
        for px in (-8.3, -4.4, -0.6, 4.4):                     # posts under the gallery
            pz = C["deck_z"] - 0.2
            wx, wz = (30.0 - pz) * er[0] + px * t[0], (30.0 - pz) * er[1] + px * t[1]
            for dy in range(0, floor_dy):
                self.put(wx, yf + dy, wz, POST)
        up = silo.facing_radial(b + math.pi / 2)                # the stair climbs toward +x
        for i, dy in enumerate((2, 1, 0)):                     # 16 steps down from x -8.5 at z 0.9..2.1
            m = (x >= -8.5 - (i + 1) * 1.6) & (x < -8.5 - i * 1.6) & (zl >= 0.9) & (zl < 2.1)
            v.mask(yf + dy, yf + dy, m, f"minecraft:polished_deepslate_stairs[facing={up},half=bottom,shape=straight,waterlogged=false]")
            for ddy in range(0, dy):
                v.mask(yf + ddy, yf + ddy, m, CONCRETE)

    def hatch(self, yf: int) -> None:
        """The round hatch, 3.2 m in radius, through the hall floor into the void (model: at the camera orbit 25.5 m
        on the bearing the descent crosses, 11.2 degrees), with its low concrete collar."""
        silo, v = self.silo, self.v
        b = bearing(18 * math.sin(2 * math.pi * 145.5 / 14))
        hx, hz = 25.5 * math.cos(b), 25.5 * math.sin(b)
        d = np.hypot(self.X - hx, self.Z - hz)
        top = silo.yi(silo.void_top_rel)
        v.mask(top, yf - 1, d < 3.2, AIR)
        v.mask(yf, yf, (d >= 3.2) & (d < 3.9), "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
        self.hatch_at = (hx, hz)

    # digger void ----------------------------------------------------------------------------------------------
    def digger_void(self) -> None:
        silo, s, v = self.silo, self.s, self.v
        top = silo.yi(silo.void_top_rel)                      # first row under the slab
        floor = silo.yi(silo.void_floor_rel)
        kx, ky = s.void_radius / 100.0, (top - floor) / 90.0  # model metres to blocks, across and up
        self.kx, self.ky, self.vfloor, self.vtop = kx, ky, floor, top
        r = silo.r
        for y in range(floor, top):                           # the cavern widens 3 m toward its floor
            rr = s.void_radius + 3 * kx * (top - y) / (top - floor)
            v.mask(y, y, r < rr, AIR)
        v.mask(floor - 1, floor - 1, r < s.void_radius + 3 * kx, ROCK)
        v.mask(floor, floor + 1, r < s.void_radius + 3 * kx, WATER)     # standing water; its surface is floor + 2
        for dh in (6, 14, 22):                                # pour lines round the wall
            y = top - 1 - int(round(dh * ky))
            v.mask(y, y, silo.ring(s.void_radius - 1, s.void_radius + 1), ROCK_DARK)
        # the roof: 28 radial girders and three ring girders under the rock (model r 32-102; rings 44, 62, 80)
        for k in range(28):
            a = k * TAU / 28
            for rr in np.arange(32 * kx, s.void_radius, 0.5):
                self.put(rr * math.cos(a), top - 1, rr * math.sin(a), ROCK_DARK)
        for R in (44, 62, 80):
            v.mask(top - 1, top - 1, silo.ring(R * kx - 0.5, R * kx + 0.5), ROCK_DARK)
        self.trusses(floor + 2)
        self.unit(floor)
        self.big_ring(floor)
        self.camp(floor)
        self.tunnel_in(floor)

    def trusses(self, y: int) -> None:
        """The truss framework across the floor at the water line: sixteen radial runs (r 48-88) and two rings (60,
        76), clear of the tunnel by 16 degrees."""
        kx = self.kx
        tun = bearing(TUN_PHI)
        for k in range(16):
            a = k * math.pi / 8 + math.pi / 16 + math.radians(FRAME_DEG)
            if abs(((a - tun + math.pi) % TAU) - math.pi) < math.radians(16):
                continue
            for rr in np.arange(48 * kx, 88 * kx, 0.5):
                self.put(rr * math.cos(a), y, rr * math.sin(a), RUST_CUT)
        for R in (60, 76):
            m = self.silo.ring(R * kx - 0.5, R * kx + 0.5)
            th = self.silo.theta
            clear = np.abs(((th - tun + math.pi) % TAU) - math.pi) >= math.radians(16)
            self.v.mask(y, y, m & clear, RUST_CUT)

    def unit(self, floor: int) -> None:
        """The grown unit (model core x CORE_S 1.8, turned CORE_ROT 16): a cage of twenty verticals and eight rings,
        working platforms (some stripped), cladding on some faces, riser pipes, eight legs (hip, knee, foot pad and
        three drills), two ladders up the cage."""
        silo, v, kx, ky = self.silo, self.v, self.kx, self.ky
        S, rot = 1.8, math.radians(16 + FRAME_DEG)
        uR, uH = 14 * S * kx, 34 * S * ky
        base = floor + max(1, int(round(1 * ky)))
        dist, ang = self.frame(0.0, 0.0, rot)
        lv = [base + int(round(i * uH / 7)) for i in range(8)]
        for y in lv:                                                   # rings
            v.mask(y, y, (dist >= uR - 0.5) & (dist < uR + 0.5), RUST)
        for k in range(20):                                            # verticals
            a = k * math.pi / 10 + rot
            x, z = uR * math.cos(a), uR * math.sin(a)
            for y in range(base, lv[-1] + 1):
                self.put(x, y, z, RUST)
        for i in range(1, 7):                                          # platforms and their rails
            a0, span = (i * 1.7) % TAU, (math.pi * 1.1 if i % 3 == 0 else TAU)
            m = (dist < uR) & (np.mod(ang - a0, TAU) < span)
            v.mask(lv[i], lv[i], m, GRATE)
            rr = (14 + 2.2) * S * kx - 0.4 * kx
            v.mask(lv[i] + 1, lv[i] + 1, (dist >= uR + 0.5) & (dist < rr) & (np.mod(ang - a0, TAU) < span), GRATE)
            v.mask(lv[i] + 2, lv[i] + 2, (dist >= rr - 0.5) & (dist < rr + 0.5) & (np.mod(ang - a0, TAU) < span), RED_RAIL)
            c0 = (i * 2.3) % TAU                                       # cladding on 0.7 pi of the face
            clad = (dist >= uR - 0.5) & (dist < uR + 0.5) & (np.mod(ang - c0, TAU) < 0.7 * math.pi)
            v.mask(lv[i] - int(uH / 7 * 0.9) + 1, lv[i], clad, RUST_CUT)
        for k in range(9):                                             # riser pipes in the cage
            a = k * 0.72 + rot
            x, z = (14 - 3.2) * S * kx * math.cos(a), (14 - 3.2) * S * kx * math.sin(a)
            y0 = base + int(round((17 + 2 - 34 * 0.25) * S * ky))
            for y in range(y0, y0 + int(round(34 * 0.5 * S * ky))):
                self.put(x, y, z, RUST_CUT)
        for k in range(8):                                             # legs
            a = k * math.pi / 4 + rot
            ca, sa = math.cos(a), math.sin(a)
            hip = ((14 - 6) * S * kx, base + (9 * S) * ky)
            knee = ((14 + 9) * S * kx, base + (25 * S) * ky)
            foot = ((14 + 26) * S * kx, floor + 2)
            P = lambda rr, y: (rr * ca, y, rr * sa)
            self.beam(P(*hip), P(*knee), 1.0, RUST)
            self.beam(P(*knee), P(*foot), 1.0, RUST)
            fr, fy = foot
            self.v.box(silo.R + int(round(fr * ca)) - 2, floor, silo.R + int(round(fr * sa)) - 2,
                       silo.R + int(round(fr * ca)) + 2, floor + 1 + 1, silo.R + int(round(fr * sa)) + 2, RUST)   # foot pad
            for j in range(3):                                         # three drills ahead of the foot
                rr = fr + (2.0 + j * 2.6) * S * kx
                aj = a + (j - 1) * 0.07
                self.put(rr * math.cos(aj), floor + 1, rr * math.sin(aj), "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=true]")
                self.put(rr * math.cos(aj), floor + 2, rr * math.sin(aj), "minecraft:pointed_dripstone[thickness=base,vertical_direction=down,waterlogged=false]")
        for la in (70, 250):                                           # ladders up the cage
            a = math.radians(la) + rot
            lx, lz = (uR + 1) * math.cos(a), (uR + 1) * math.sin(a)
            f = silo.facing_radial(a)
            dx, dz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[f]
            for y in range(floor + 2, lv[-1] + 1):
                if self.get(lx - dx, y, lz - dz) == AIR:
                    self.put(lx - dx, y, lz - dz, RUST)
                self.put(lx, y, lz, f"minecraft:ladder[facing={f},waterlogged=false]")
        from bays import seeded
        SR, SH = uR, uH                                                # person-sized lamps all over the grown unit
        for k in range(220):
            a = seeded(k, 3) * TAU + rot
            h = base + 1 + seeded(k, 4) * (SH - 2)
            rr = SR + (seeded(k, 5) - 0.5) * 1.6
            x, z, y = rr * math.cos(a), rr * math.sin(a), int(round(h))
            if self.get(x, y, z) == AIR:
                self.put(x, y, z, "minecraft:end_rod[facing=up]")
        for k in range(8):                                             # its eight work lamps, amber and cold
            a = (k + 0.5) * math.pi / 4 + rot
            x, z = 23 * S * kx * math.cos(a), 23 * S * kx * math.sin(a)
            y = base + int(round((26.7 if k % 2 else 21.8) * S * ky))
            self.put(x, y, z, "minecraft:shroomlight" if k % 2 else "minecraft:sea_lantern")
        self.unit_top = lv[-1]

    def big_ring(self, floor: int) -> None:
        """The ring at the excavation edge (model r 90, 9 m up, tube 2.6 m) with a gap where the way to the bore
        crosses, forty hanging drills and eight struts in to the unit."""
        silo, v, kx, ky = self.silo, self.v, self.kx, self.ky
        rot = math.radians(22.5 + FRAME_DEG)
        R, y = 90 * kx, floor + int(round(9 * ky))
        tube = max(1.0, 2.6 * kx)
        dist, ang = self.frame(0.0, 0.0, rot)
        gap_c, gap = math.radians(TUN_PHI) + math.pi / 8 - math.radians(7), math.radians(18)
        off = np.abs(((ang - gap_c + math.pi) % TAU) - math.pi)
        for dy in range(-int(tube), int(tube) + 1):
            w = math.sqrt(max(0.0, tube ** 2 - dy ** 2))
            v.mask(y + dy, y + dy, (np.abs(dist - R) <= w) & (off >= gap), RUST)
        for k in range(40):
            a = k * math.pi / 20
            if abs(((a - gap_c + math.pi) % TAU) - math.pi) < gap + math.radians(3):
                continue
            x, z = R * math.cos(a + rot), R * math.sin(a + rot)
            for dy in range(1, 3):
                self.put(x, y - int(tube) - dy, z, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]" if dy == 2 else
                         "minecraft:pointed_dripstone[thickness=base,vertical_direction=down,waterlogged=false]")
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            if abs(((a - gap_c + math.pi) % TAU) - math.pi) < gap:
                continue
            ca, sa = math.cos(a + rot), math.sin(a + rot)
            self.beam((24 * kx * ca, y, 24 * kx * sa), (R * ca, y, R * sa), 0.5, RUST)
        for k in range(10):                                            # bulbs along the ring's top
            a = k * math.pi / 5 + 0.3
            if abs(((a - gap_c + math.pi) % TAU) - math.pi) < gap:
                continue
            self.put(R * math.cos(a + rot), y + int(tube) + 1, R * math.sin(a + rot), LANTERN)
        for e in (gap_c - gap, gap_c + gap):                           # the ring's two ends, each with a lamp
            x, z = R * math.cos(e + rot), R * math.sin(e + rot)
            self.put(x, y + int(tube) + 1, z, LANTERN)

    def camp(self, floor: int) -> None:
        """George's camp on a concrete slab 9 x 7 m rising out of the water (model 150 degrees, r footR + 10),
        square to the world: a cot with a blanket, a stack of crates, a jerrycan, papers, a low table, a bulb."""
        a = bearing(150)
        r = (14 + 26 + 10) * self.kx
        cx, cz = int(round(r * math.cos(a))), int(round(r * math.sin(a)))
        R, v, y = self.silo.R, self.v, floor + 2
        v.box(R + cx - 4, floor, R + cz - 3, R + cx + 4, y, R + cz + 3, CONCRETE_DARK)
        top = y + 1
        put = lambda dx, dz, dy, st: v.set(R + cx + dx, top + dy, R + cz + dz, st)
        put(3, 2, 0, "minecraft:gray_bed[facing=west,occupied=false,part=head]")      # cot at (2.8, 2.0)
        put(4, 2, 0, "minecraft:gray_bed[facing=west,occupied=false,part=foot]")
        put(-3, 2, 0, "minecraft:barrel[facing=up,open=false]")                       # crates at (-2.9, 1.9), (-2.1, 2.3)
        put(-3, 2, 1, "minecraft:barrel[facing=up,open=false]")
        put(-2, 2, 0, "minecraft:barrel[facing=up,open=false]")
        put(-1, 2, 0, "minecraft:cauldron")                                           # jerrycan at (-1.3, 2.4)
        for dx in (0, 1):
            put(dx, 0, 0, "minecraft:waxed_weathered_cut_copper_slab[type=bottom,waterlogged=false]")   # table 2.0 x 0.9
        for dx, dz in ((0, 2), (1, 3), (-1, 3)):
            put(dx, dz, 0, "minecraft:light_gray_carpet")                             # papers
        put(-1, 1, 0, POST)                                                           # the bulb at (-1.2, 2.5, 0.9)
        put(-1, 1, 1, LANTERN)

    def tunnel_cells(self, x: np.ndarray, z: np.ndarray):
        """Along (metres from the axis on the bore's bearing) and lateral offset of columns at x, z."""
        b = bearing(TUN_PHI)
        return x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)

    def tunnel_in(self, floor: int) -> None:
        """The part of the bore inside the silo's volume."""
        self.tunnel_into(self.v, self.silo.R, floor)

    def tunnel_into(self, vol: Volume, cx: int, floor: int, cz: int | None = None) -> None:
        """Carve and furnish the bore into `vol`, whose column (cx, cz) is the silo axis and row `floor` the void
        floor. From the cavern (r void_radius - 2) out 68 m: concrete lining 1.4 m thick, a portal frame at its
        mouth, seven ribs, three amber lamps under the roof, water at the cavern's level, and at the far end the
        door: a steel leaf 8.6 x 6.4 m with five ribs and two rails in a frame, a faint light at its edge."""
        cz = cx if cz is None else cz
        sx, sy, sz = vol.size
        X, Z = np.meshgrid(np.arange(sx) - cx, np.arange(sz) - cz, indexing="ij")
        along, lat = self.tunnel_cells(X.astype(float), Z.astype(float))
        r0 = self.s.void_radius - 2
        r1 = r0 + TUN_LEN
        H = int(round(TUN_H))                                         # rows above the floor row
        span = (along >= r0) & (along < r1)
        bore = span & (np.abs(lat) < TUN_HW)
        lining = span & (np.abs(lat) < TUN_HW + 1.4) & ~bore
        for y in range(floor - 1, floor + H + 2):
            vol.mask(y, y, lining | (bore & ((y < floor) | (y > floor + H))), CONCRETE_DARK)
        vol.mask(floor, floor, bore, CONCRETE_DARK)                   # bore floor, 0.7 m under the water
        vol.mask(floor + 1, floor + 1, bore, WATER)
        for y in range(floor + 2, floor + H + 1):
            vol.mask(y, y, bore, AIR)
        mouth = (along >= r0) & (along < r0 + 2) & (np.abs(lat) < TUN_HW + 1.5)
        for y in range(floor + 1, floor + H + 3):                    # portal frame, standing proud in the cavern
            vol.mask(y, y, mouth & ((np.abs(lat) >= TUN_HW) | (y > floor + H)), CONCRETE)
        for k in range(1, 8):                                         # ribs every 8.5 m
            a = r0 + k * TUN_LEN / 8
            rib = (np.abs(along - a) < 0.5) & (np.abs(lat) < TUN_HW)
            vol.mask(floor + H, floor + H, rib, CONCRETE)
            for y in range(floor + 2, floor + H):
                vol.mask(y, y, rib & (np.abs(lat) >= TUN_HW - 0.6), CONCRETE)
        for a in (r0 + 16, r0 + 42, r1 - 6):                           # amber lamps under the roof
            lamp = (np.abs(along - a) < 0.5) & (np.abs(lat) < 0.5)
            vol.mask(floor + H, floor + H, lamp, HANG)
        dx = r1 - 1.1                                                 # the door, its leaf 1.0 m thick
        leaf = (np.abs(along - dx) < 0.5) & (np.abs(lat) < (TUN_HW * 2 - 0.6) / 2)
        frame = (np.abs(along - dx) < 0.8) & (np.abs(lat) < TUN_HW) & ~leaf
        dh = int(round(TUN_H - 0.8))
        for y in range(floor + 1, floor + 1 + dh):
            vol.mask(y, y, frame, CONCRETE)
            vol.mask(y, y, leaf, RUST)
        ribs = leaf & (np.mod(lat + 0.5, (TUN_HW * 2 - 0.6) / 5.6 * 2) < 1.0)
        for y in range(floor + 2, floor + dh):
            vol.mask(y, y, ribs, RUST_CUT)
        for y in (floor + 2, floor + dh - 1):
            vol.mask(y, y, leaf, RUST_CUT)
        vol.mask(floor + 1 + dh, floor + H, (np.abs(along - dx) < 0.8) & (np.abs(lat) < TUN_HW), CONCRETE)
        edge = (np.abs(along - (dx - 1)) < 0.5) & (np.abs(lat) < TUN_HW) & (np.abs(lat) >= TUN_HW - 1.0)
        vol.mask(floor + 3, floor + 3, edge, "minecraft:light[level=6,waterlogged=false]")   # faint light at the edge
        beyond = (along >= r1) & (along < r1 + 1) & (np.abs(lat) < TUN_HW + 1.4)
        for y in range(floor - 1, floor + H + 2):
            vol.mask(y, y, beyond, CONCRETE_DARK)
