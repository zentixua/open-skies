# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""The complex's surroundings in the show's 2052 aerial (S3E09 frame 01, aerial2052-1920.jpg, 1920x802): the gate,
its parking loop, the perimeter roads, the railway and its yard, and the facility yards (hangars, tank farms, sheds,
vehicle yards), read by eye in frame pixels and taken onto the ground through the frame's homography
(canon/fit.json Hf1920). Writes canon/surroundings.json in metres about Silo 1's ring centre in the canon frame
(x east, z south, gate north; edge 270 m) for surroundings.py.

Heights: the homography is decomposed into a camera (square pixels, principal point at the frame centre; one focal
length; the fit's 7.5 % departure from a true rotation is the height error), which gives pixels per metre of height
at each ground point; a feature's visible vertical extent in pixels (v) becomes metres.

Accuracy (say it with every number): the frame fit has 11 px rms on ring centres; at the frame's top one pixel of
depth is 8-10 m and at its bottom 3-4 m, across 1.7-2.6 m. Edges are read to about 2 px. So: across +-5 m, depth
+-10 m near the field, +-30 m beyond it, +-100 m at the gate (see `gate_note`). Heights +-30 %.

  python3 canon_surroundings.py [--png top.png]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIT = json.load(open(os.path.join(HERE, "canon", "fit.json")))
H = np.array(FIT["Hf1920"])
HI = np.linalg.inv(H)
EDGE = 270.0
W, HT = 1920, 802


def ground(px: float, py: float) -> tuple[float, float]:
    """Frame pixel -> metres east, south of Silo 1 (canon frame)."""
    q = HI @ np.array([px, py, 1.0])
    return float(q[0] / q[2] * EDGE), float(q[1] / q[2] * EDGE)


def camera():
    """Focal length and pose from Hf1920 = K [r1 r2 t] (ground in canon units), K with square pixels and the
    principal point at the frame centre. Returns (K, R, t, err): err is the departure of r1, r2 from orthonormal."""
    cx, cy = W / 2, HT / 2
    best = None
    for f in np.linspace(300, 6000, 11401):
        M = np.linalg.inv(np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])) @ H
        a, b = M[:, 0], M[:, 1]
        e = abs(a @ b) / (np.linalg.norm(a) * np.linalg.norm(b)) + abs(np.linalg.norm(a) / np.linalg.norm(b) - 1)
        if best is None or e < best[0]:
            best = (e, f)
    e, f = best
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
    M = np.linalg.inv(K) @ H
    s = 2 / (np.linalg.norm(M[:, 0]) + np.linalg.norm(M[:, 1]))
    r1, r2, t = M[:, 0] * s, M[:, 1] * s, M[:, 2] * s
    if t[2] < 0:
        r1, r2, t = -r1, -r2, -t
    return K, np.c_[r1, r2, np.cross(r1, r2)], t, e


K, ROT, T, CAM_ERR = camera()


def px_per_m_up(x: float, z: float) -> float:
    """Image pixels per metre of height at ground point x, z (metres). Up is -r3 in this x-east z-south frame."""
    def proj(h):
        q = K @ (ROT @ np.array([x / EDGE, z / EDGE, -h / EDGE]) + T)
        return q[:2] / q[2]
    return float(np.linalg.norm(proj(10) - proj(0)) / 10)


def m_per_px_across(px: float, py: float) -> float:
    a, b = np.array(ground(px - 5, py)), np.array(ground(px + 5, py))
    return float(np.linalg.norm(b - a) / 10)


def rect(c, w, h):
    return [(c[0] - w / 2, c[1] - h / 2), (c[0] + w / 2, c[1] - h / 2), (c[0] + w / 2, c[1] + h / 2), (c[0] - w / 2, c[1] + h / 2)]


# Read by eye from 3-8x crops with a 10 px grid. poly = footprint at the ground (for buildings the base, not the
# roof), line = centre line, points = centres at the ground; v = visible vertical extent of a side in pixels.
FEATURES = [
    # the gate at the north end of the axis avenue (frame 02 for what frame 01 cannot resolve, see gate_note)
    dict(id="gate_paved", kind="paved", group="gate", poly=[(885, 18), (872, 24), (866, 35), (868, 48), (875, 55), (890, 59), (905, 57), (915, 52), (918, 45), (912, 33), (903, 23), (890, 17)],
         what="the coach park: asphalt round the lawn, the access road widening into it (frame 02: 3-4 lanes each way with grass medians, ~35 coaches)"),
    dict(id="gate_lawn", kind="lawn", group="gate", ellipse=[(875, 48), (915, 48), (895, 40), (895, 56)],
         what="the oval lawn the loop goes round"),
    dict(id="gate_forecourt", kind="paved", group="gate", poly=[(882, 58), (910, 57), (909, 66), (884, 66)],
         what="forecourt in front of the canopy, where the crowd stands (frame 02)"),
    dict(id="gate_canopy", kind="canopy", group="gate", line=[(885, 67), (909, 67)], peaks=5,
         what="white tensile canopy over the entrance, 5-6 peaks on low arches (frame 02)"),
    dict(id="gate_band", kind="band", group="gate", line=[(829, 70), (964, 70)],
         what="long low grey band either side of the canopy (frame 02: wall or fence, uncertain)"),
    dict(id="gate_pads_w", kind="round_pad", group="gate", points=[(743, 79), (764, 79), (787, 78)], d_px=10,
         what="three white rings with dark centres west of the avenue (fountains, planters or pads: uncertain)"),
    dict(id="gate_pads_e", kind="round_pad", group="gate", points=[(1010, 73), (1029, 73), (1052, 73)], d_px=10,
         what="the same three east of the avenue"),
    dict(id="access_road", kind="road", group="gate", line=[(885, 18), (886, 0)], lanes=4,
         what="the access road north through the forest, two lanes each way with a yellow centre line (frame 02)"),
    # roads
    dict(id="road_north", kind="road", group="roads", line=[(700, 73), (800, 66), (893, 62), (980, 62), (1137, 67), (1240, 80), (1310, 98), (1460, 125), (1600, 160), (1700, 190), (1760, 214)],
         what="perimeter road along the north edge, past the gate to the north-east halls and yard"),
    dict(id="road_south", kind="road", group="roads", line=[(300, 800), (500, 799), (667, 777), (944, 749), (1111, 740), (1311, 733), (1520, 736), (1920, 735)],
         what="perimeter road along the south edge, light masts and parked white vans on it"),
    dict(id="road_se", kind="road", group="roads", line=[(1450, 736), (1520, 700), (1560, 650), (1600, 615), (1660, 603), (1750, 580)],
         what="gravel road up the west side of the south-east yard"),
    dict(id="road_sw", kind="road", group="roads", line=[(160, 598), (215, 588), (255, 590), (272, 608), (280, 640), (282, 662), (300, 690), (330, 728)],
         what="gravel road from the west woods round to the mast pad and the south-west hangar"),
    dict(id="road_sw_south", kind="road", group="roads", line=[(372, 705), (430, 708), (480, 722), (530, 752), (560, 770)],
         what="gravel road from the mast pad south-east down to the south road"),
    dict(id="road_e", kind="road", group="roads", line=[(1745, 475), (1752, 520), (1765, 560), (1790, 578)],
         what="road down the east side from the pond to the south-east yard"),
    # north-west: the railway and its yard
    dict(id="rail_main", kind="rail", group="nw", line=[(0, 295), (80, 262), (160, 228), (240, 192), (330, 152), (420, 122), (520, 104), (640, 86), (700, 75)], tracks=2,
         what="railway along the north-west edge (two pale lines in the corridor; track count uncertain)"),
    dict(id="rail_yard", kind="rail", group="nw", line=[(120, 240), (330, 152)], tracks=4,
         what="sidings fanning out in the yard (3-4 lines visible)"),
    dict(id="nw_yard", kind="gravel", group="nw", poly=[(150, 170), (230, 155), (300, 148), (325, 153), (290, 195), (250, 215), (190, 215), (150, 205)],
         what="rail yard: grey gravel"),
    dict(id="nw_strip", kind="gravel", group="nw", poly=[(0, 250), (60, 225), (160, 205), (170, 215), (120, 250), (40, 300), (0, 310)],
         what="gravel strip beside the line south-west of the yard"),
    dict(id="nw_shed_a", kind="shed", group="nw", poly=[(214, 203), (248, 195), (252, 200), (218, 208)], v=3, what="long gabled shed by the sidings"),
    dict(id="nw_shed_b", kind="shed", group="nw", poly=[(224, 197), (258, 189), (262, 194), (228, 202)], v=3, what="its twin"),
    dict(id="nw_domes", kind="dome", group="nw", points=[(303, 208), (316, 212)], d_px=10, v=6, what="two round storage domes (one blue-grey, one white)"),
    dict(id="nw_depot", kind="vehicle_rows", group="nw", poly=[(462, 122), (520, 118), (528, 168), (458, 170)], what="vehicle depot: dark vehicles in rows in a forest clearing"),
    dict(id="n_hall", kind="shed", group="nw", poly=[(581, 97), (606, 106), (603, 112), (578, 103)], v=4, what="long hall with a blue-grey roof by the road"),
    dict(id="n_tanks", kind="tank", group="nw", points=[(563, 106), (571, 110)], d_px=6, v=4, what="two small white tanks beside it"),
    # north-east: halls, car park, yard, tank farm
    dict(id="ne_hall_1", kind="barrel_hall", group="ne", poly=rect((1333, 114), 32, 14), v=8, what="largest white barrel-roofed hall"),
    dict(id="ne_hall_2", kind="barrel_hall", group="ne", poly=rect((1360, 110), 22, 12), v=6, what="barrel hall behind it"),
    dict(id="ne_block", kind="shed", group="ne", poly=rect((1362, 131), 44, 10), v=4, what="flat dark-roofed block joining the halls"),
    dict(id="ne_hall_3", kind="barrel_hall", group="ne", poly=rect((1397, 129), 26, 14), v=7, what="barrel hall"),
    dict(id="ne_hall_4", kind="barrel_hall", group="ne", poly=rect((1420, 133), 26, 14), v=7, what="barrel hall"),
    dict(id="ne_carpark", kind="vehicle_rows", group="ne", poly=[(1465, 128), (1600, 158), (1705, 192), (1700, 207), (1595, 190), (1480, 152)], what="large car park, dense rows of dark vehicles"),
    dict(id="ne_carpark_2", kind="vehicle_rows", group="ne", poly=[(1228, 84), (1300, 88), (1300, 96), (1228, 92)], what="a row of parked vehicles north of the pond"),
    dict(id="ne_shelters", kind="shelter_rows", group="ne", poly=[(1535, 173), (1592, 178), (1600, 193), (1545, 191)], what="rows of flat grey roofs at the car park's south edge (shelters, uncertain)"),
    dict(id="ne_yard", kind="gravel", group="ne", poly=[(1625, 213), (1700, 205), (1770, 215), (1830, 220), (1890, 240), (1890, 300), (1840, 295), (1800, 280), (1760, 260), (1700, 240), (1650, 232)], what="gravel yard"),
    dict(id="ne_shed", kind="shed", group="ne", poly=[(1666, 213), (1703, 230), (1699, 236), (1662, 219)], v=4, what="long shed with a light roof"),
    dict(id="ne_tanks", kind="tank", group="ne", points=[(1820, 262), (1840, 272), (1862, 280)], d_px=16, v=6, what="tank farm: three white tanks in a row"),
    # south-west: vehicle yard, hangar, tanks, mast pad, domes
    dict(id="sw_vehicle_yard", kind="vehicle_rows", group="sw", poly=[(0, 655), (70, 660), (130, 690), (160, 705), (205, 712), (208, 745), (160, 758), (0, 760)], what="vehicle yard: many rows of vehicles or huts on curved lanes"),
    dict(id="sw_shed", kind="shed", group="sw", poly=[(60, 657), (90, 667), (88, 672), (58, 662)], v=3, what="long low shed at the yard's north edge"),
    dict(id="sw_building", kind="shed", group="sw", poly=[(100, 678), (126, 682), (128, 697), (102, 694)], v=5, what="blue-roofed building in the yard"),
    dict(id="sw_mast_pad", kind="gravel", group="sw", poly=[(288, 655), (318, 648), (372, 684), (366, 705), (330, 708), (292, 672)], what="pale pad with two masts and equipment"),
    dict(id="sw_masts", kind="mast", group="sw", points=[(343, 690), (361, 692)], v_each=[40, 27], what="two tall lattice masts on the pad"),
    dict(id="sw_yard", kind="gravel", group="sw", poly=[(230, 725), (330, 715), (372, 735), (372, 800), (220, 800)], what="gravel apron of the hangar"),
    dict(id="sw_hangar", kind="barrel_hall", group="sw", poly=[(272, 735), (306, 731), (320, 768), (286, 775)], v=12, what="large white barrel-roofed hangar"),
    dict(id="sw_flat", kind="shed", group="sw", poly=[(306, 758), (330, 752), (345, 780), (320, 787)], v=5, what="flat-roofed building beside it, white vehicles parked in front"),
    dict(id="sw_tanks", kind="tank", group="sw", points=[(271, 740), (261, 746), (251, 757), (246, 766)], d_px=11, v=9, what="four white tanks on the hangar's west side"),
    dict(id="sw_domes", kind="dome", group="sw", points=[(22, 550), (33, 553), (104, 550)], d_px=8, v=6, what="white domes in the west woods"),
    # south-east: yard, hangar, tanks
    dict(id="se_yard", kind="gravel", group="se", poly=[(1520, 700), (1560, 650), (1600, 615), (1650, 603), (1700, 592), (1750, 578), (1800, 572), (1920, 585), (1920, 735), (1520, 737)], what="large bare gravel yard (runs on past the frame edge)"),
    dict(id="se_hangar", kind="barrel_hall", group="se", poly=rect((1773, 676), 50, 22), v=10, what="large white barrel-roofed hangar"),
    dict(id="se_block", kind="shed", group="se", poly=rect((1757, 692), 30, 12), v=5, what="flat grey block in front of it, white vehicles beside"),
    dict(id="se_tanks_a", kind="tank", group="se", points=[(1727, 690), (1740, 696), (1756, 704)], d_px=13, v=6, what="three white tanks by the hangar"),
    dict(id="se_tanks_b", kind="tank", group="se", points=[(1675, 626), (1687, 624), (1698, 622)], d_px=13, v=8, what="three white tanks at the yard's north side"),
    dict(id="se_building", kind="shed", group="se", poly=rect((1728, 606), 36, 16), v=5, what="blue-grey roofed building"),
    dict(id="se_stacks", kind="vehicle_rows", group="se", polys=[rect((1705, 652), 50, 16), rect((1850, 652), 60, 24), rect((1645, 701), 90, 20), rect((1550, 701), 40, 20)],
         what="groups of dark rectangular objects in rows (vehicles or containers, uncertain)"),
    dict(id="s_bare", kind="bare", group="s", poly=[(940, 735), (1300, 722), (1520, 725), (1520, 760), (1300, 760), (940, 775)], what="bare earth and gravel strip along the south road"),
    dict(id="s_masts", kind="mast", group="s", points=[(747, 735), (944, 719), (1136, 708)], what="light masts along the south road (height not measurable: tops blur into the background)"),
]

# frame 02 (looking in along the axis): read relative to the canopy and lawn, scaled by frame 01 (see gate_note)
GATE_NOTE = (
    "The gate is the frame's farthest point and its least certain. Through Hf1920 the canopy is at 1.52 km north of "
    "Silo 1; layout.json's gate (canon_layout gate, -4.993 edges = 1.35 km) comes from the joint fit with the founders' "
    "plaque, whose own frame residual at the gate is 25 px: the 2052 frame puts it 170 m farther. Here the gate group "
    "stays where the frame shows it and surroundings.py carries the avenue on from layout's gate to the canopy. "
    "Scale near the gate disagrees between frames: frame 01 gives the lawn 100 m across, frame 02 by coach sizes "
    "(width 2.55 m, length 12 m) about 63 m; s3e09/notes.md read 7 coach lengths, 85 m. Sizes in this group are "
    "frame 01's, which is consistent with every other feature here; frame 02 gives what frame 01 cannot resolve "
    "(lane counts, canopy peaks and height, the band, coaches).")

# heights frame 01 cannot give
FRAME02 = {
    "gate_canopy": {"height_m": 13, "how": "frame 02: peaks 38 px over their base at about 3 px/m (scale from the lawn's 85 m)"},
    "access_road": {"width_m": 15, "how": "frame 02: 2+2 lanes of 3.5 m and a centre line; it widens to 3-4 lanes each way with grass medians into the coach park"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "canon", "surroundings.json"))
    ap.add_argument("--png", help="top-down sketch with the rings, for a look")
    a = ap.parse_args()
    items = []
    for f in FEATURES:
        it = {k: v for k, v in f.items() if k not in ("poly", "polys", "line", "points", "ellipse", "v", "v_each", "d_px")}
        src = {k: f[k] for k in ("poly", "polys", "line", "points", "ellipse") if k in f}
        it["source_px"] = src
        if "poly" in f:
            it["poly"] = [[round(c, 1) for c in ground(*p)] for p in f["poly"]]
        if "polys" in f:
            it["polys"] = [[[round(c, 1) for c in ground(*p)] for p in q] for q in f["polys"]]
        if "line" in f:
            it["line"] = [[round(c, 1) for c in ground(*p)] for p in f["line"]]
        if "ellipse" in f:
            l, r, t, b = [np.array(ground(*p)) for p in f["ellipse"]]
            c = (l + r + t + b) / 4
            it["centre"] = [round(float(v), 1) for v in c]
            it["axes_m"] = [round(float(np.linalg.norm(r - l)), 1), round(float(np.linalg.norm(b - t)), 1)]
            it["angle_deg"] = round(math.degrees(math.atan2(r[1] - l[1], r[0] - l[0])), 1)
        if "points" in f:
            it["points"] = [[round(c, 1) for c in ground(*p)] for p in f["points"]]
            if "d_px" in f:
                it["diameter_m"] = round(float(np.mean([f["d_px"] * m_per_px_across(*p) for p in f["points"]])), 1)
        # heights
        anchor = (f.get("points") or f.get("poly") or f.get("line") or f.get("ellipse") or f["polys"][0])[0]
        gx, gz = ground(*anchor)
        ppm = px_per_m_up(gx, gz)
        if "v" in f:
            it["height_m"] = round(f["v"] / ppm, 1)
            it["height_how"] = f"{f['v']} px of side at {ppm:.2f} px per metre up (camera from Hf1920), +-30 %"
        if "v_each" in f:
            hs = [None if v is None else round(v / px_per_m_up(*ground(*p)), 1) for v, p in zip(f["v_each"], f["points"])]
            it["heights_m"] = hs
            if any(h is not None for h in hs):
                it["height_how"] = "px of the mast from base to tip / px per metre up (camera from Hf1920), +-30 %"
        if f["kind"] == "road" and "width_m" not in it:
            it["width_m"] = 7
            it["width_how"] = "2-3 px at 2-2.5 m/px across: two lanes; not finer than that"
        if f["kind"] == "rail":
            it["gauge_m"] = 1.435
            it["track_spacing_m"] = 4.5
            it["spacing_how"] = "standard gauge and track centres; the frame resolves only the corridor"
        if f["id"] in FRAME02:
            it.update(FRAME02[f["id"]])
        it["m_per_px_across"] = round(m_per_px_across(*anchor), 2)
        items.append(it)
    # the avenue runs straight from the canopy to Silo 1 (frames 01, 02; the plaque's axis), so the gate group sits on
    # x = 0: its frame position is 10-15 m east of the axis, inside the frame's +-5 m across plus the fit's 11 px rms
    can = next(i for i in items if i["id"] == "gate_canopy")["line"]
    shift = -(can[0][0] + can[1][0]) / 2
    for it in items:
        if it["group"] != "gate":
            continue
        for key in ("poly", "line", "points"):
            if key in it:
                it[key] = [[round(p[0] + shift, 1), p[1]] for p in it[key]]
        if "centre" in it:
            it["centre"][0] = round(it["centre"][0] + shift, 1)
        it["shifted_x_m"] = round(shift, 1)
    unsized = [
        {"what": "gate depth layout", "why": GATE_NOTE},
        {"what": "barrel-hall heights", "why": "end faces are 6-12 px; heights given are side extents at +-30 %, and the arch's rise cannot be told from wall height"},
        {"what": "light and radio masts along the field edges and the south road", "why": "tops blur into the background except the two on the south-west pad; their bases are at the points given"},
        {"what": "vehicles, coaches, huts in the yards and car parks", "why": "rows are resolved, single vehicles are not (one coach is 5 px); counts not given"},
        {"what": "rail beyond the north-west yard", "why": "past x 700 px the corridor reads as one pale road; whether the line goes on east of the gate is not visible"},
        {"what": "round white pads by the gate", "why": "purpose unknown; size from frame 01 only"},
        {"what": "anything past the frame's left, right and bottom edges", "why": "the south-east yard and the south-west vehicle yard run on past the edge; the frame gives no more"},
        {"what": "fences round the yards", "why": "none visible at this resolution"},
    ]
    out = {
        "about": "Surroundings of the 50-silo complex in the show's 2052 aerial (S3E09 frame 01), measured in metres about "
                 "Silo 1's ring centre in the canon frame: x east, z south, the gate north; flower edge 270 m. "
                 "World = Silo 1 + R(layout rotation) * (x, z) * layout spacing / 270. Written by canon_surroundings.py; "
                 "built by surroundings.py.",
        "edge_m": EDGE,
        "frame": "aerial2052-1920.jpg = /mnt/project-files/silo/frames/s3e09/01-aerial-complex.jpg, homography canon/fit.json Hf1920",
        "camera": {"focal_px": round(float(K[0, 0]), 1), "pose_error": round(CAM_ERR, 3),
                   "height_m": round(abs(float((ROT.T @ T)[2])) * EDGE),
                   "note": "for heights only; up is -z of the fit's frame"},
        "accuracy": "across +-5 m; depth +-10 m near the field, +-30 m at the yards beyond it, +-100 m at the gate; heights +-30 %",
        "gate_note": GATE_NOTE,
        "items": items,
        "unsized": unsized,
    }
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"{a.out}: {len(items)} items; camera f {K[0, 0]:.0f} px, height {out['camera']['height_m']:.0f} m, pose error {CAM_ERR:.3f}")
    for it in items:
        ext = it.get("poly") or it.get("line") or it.get("points") or ([it["centre"]] if "centre" in it else sum(it["polys"], []))
        xs = [p[0] for p in ext]; zs = [p[1] for p in ext]
        extra = " ".join(f"{k}={it[k]}" for k in ("height_m", "heights_m", "diameter_m", "axes_m", "width_m") if k in it)
        print(f"  {it['id']:16s} {it['kind']:13s} x {min(xs):7.0f}..{max(xs):7.0f} z {min(zs):7.0f}..{max(zs):7.0f} {extra}")
    if a.png:
        sketch(out, a.png)


def sketch(out: dict, path: str) -> None:
    import cv2
    s = 0.25                                  # px per metre
    X0, Z0, X1, Z1 = -2400, -2300, 2600, 1700
    img = np.full((int((Z1 - Z0) * s), int((X1 - X0) * s), 3), (70, 120, 70), np.uint8)
    P = lambda p: (int((p[0] - X0) * s), int((p[1] - Z0) * s))
    for k, (u, v) in FIT["ground"].items():
        if k != "gate":
            cv2.circle(img, P((u * EDGE, v * EDGE)), int(110 * s), (200, 220, 200), 1)
    col = {"gravel": (150, 150, 150), "paved": (60, 60, 60), "bare": (110, 140, 160), "vehicle_rows": (40, 40, 90),
           "lawn": (60, 170, 60), "shelter_rows": (130, 130, 130)}
    for it in out["items"]:
        for q in ([it["poly"]] if "poly" in it else []) + it.get("polys", []):
            c = col.get(it["kind"], (240, 240, 240))
            cv2.fillPoly(img, [np.array([P(p) for p in q], np.int32)], c)
    for it in out["items"]:
        if "line" in it:
            c = {"rail": (30, 60, 120), "road": (210, 210, 210)}.get(it["kind"], (255, 255, 255))
            cv2.polylines(img, [np.array([P(p) for p in it["line"]], np.int32)], False, c, 2)
        for p in it.get("points", []):
            cv2.circle(img, P(p), max(2, int(it.get("diameter_m", 8) * s / 2)), (255, 255, 255), -1)
        if "centre" in it:
            cv2.ellipse(img, P(it["centre"]), (int(it["axes_m"][0] * s / 2), int(it["axes_m"][1] * s / 2)), it["angle_deg"], 0, 360, (60, 170, 60), -1)
    cv2.imwrite(path, img)


if __name__ == "__main__":
    main()
