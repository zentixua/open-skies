# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""Measure the straight paths and the rosettes of the 2052 complex on the show's 1920 aerial (branch silo-canon-img,
aerial2052-1920.jpg) through its homography (canon/fit.json Hf1920: canon ground units -> image pixels). Writes
canon/lines.json.

A homography maps straight lines to straight lines, so whether a path is straight, and whether it runs through a ring's
centre, is read off the frame itself; only absolute positions and angles carry the homography's error.

Method:
- the pale path is a ridge in (grey - Gaussian blur, sigma 3 px) x (1 - saturation); a nearly level path is drawn
  as a staircase of pixel rows, so the samples saw-tooth by up to +-0.006 units (1.7 m) about the line;
- a line: across a hypothesis drawn by eye, every 0.005 units the ridge's peak (sub-pixel) within +-0.04 units is
  taken back to the ground; a total-least-squares line is fitted with 2.5 sigma rejection, and the line's extent is
  the longest run of inliers (within 3.2 m) with gaps under 0.15 units (junctions, shade);
- a ring: radial profiles every 2.5 degrees, peak within r 0.36-0.48 units, circle fitted with rejection (the paths
  that meet the circle are rejected as outliers);
- a rosette: the same, outer circle searched at r 0.08-0.22, and the radial profile (mean over angles) counted for
  concentric rings.

Errors given per item: `fit` (the ridge's scatter about the line or circle), and `abs_m`, the homography's own error
from 50 rings: measured ring centres against canon ground (fit.json) after the best similarity, 6.1 m rms, 12.2 m max.

  uv run tools/silo/canon_lines.py AERIAL.jpg [--layout LAYOUT.json] [--png overlay.png]

Canon units: Silo 1 (fit point) at 0,0, flower edge 1, x east, y south, gate north (-y). World: Silo 1 + R(rot) *
spacing * u from the layout (default: the 1:1 site, Silo 1 at 3248,-2800, rotation 128, spacing 270).
"""
from __future__ import annotations

import argparse
import json
import math
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIT = json.load(open(os.path.join(HERE, "canon", "fit.json")))
H = np.array(FIT["Hf1920"])
G = {k: np.array(v) for k, v in FIT["ground"].items()}
ap = argparse.ArgumentParser()
ap.add_argument("aerial")
ap.add_argument("--layout")
ap.add_argument("--png")
a = ap.parse_args()
if a.layout:
    L = json.load(open(a.layout))
    one_s = next(s for s in L["silos"] if s["number"] == 1)
    ONE, ROT, EDGE = tuple(one_s["ring"]), L["rotation_deg"], L["spacing"]
else:
    ONE, ROT, EDGE = (3248.0, -2800.0), 128.0, 270.0
im = cv2.imread(a.aerial)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
sat = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[..., 1].astype(np.float32)
RID = (g - cv2.GaussianBlur(g, (0, 0), 3)) * (1.0 - sat / 255.0)


def P(u, v):
    q = H @ np.array([u, v, np.ones_like(u)])
    return q[0] / q[2], q[1] / q[2]


def samp(u, v):
    x, y = P(np.asarray(u, float), np.asarray(v, float))
    return cv2.remap(RID, x.astype(np.float32).reshape(-1, 1), y.astype(np.float32).reshape(-1, 1),
                     cv2.INTER_LINEAR).ravel()


def world(u):
    c, s = math.cos(math.radians(ROT)), math.sin(math.radians(ROT))
    return [round(ONE[0] + EDGE * (u[0] * c - u[1] * s), 1), round(ONE[1] + EDGE * (u[0] * s + u[1] * c), 1)]


def peak(r):
    i = int(np.argmax(r))
    if not 0 < i < len(r) - 1 or r[i] < 1.5 * max(1e-3, float(np.median(np.abs(r)))):
        return None
    y0, y1, y2 = r[i - 1], r[i], r[i + 1]
    den = y0 - 2 * y1 + y2
    return i + (0.5 * (y0 - y2) / den if den else 0.0)


def ridge(a_, b_, half=0.04, step=0.005):
    a_, b_ = np.array(a_, float), np.array(b_, float)
    d = b_ - a_
    n_ = np.linalg.norm(d)
    t = d / n_
    nrm = np.array([-t[1], t[0]])
    offs = np.linspace(-half, half, 81)
    out = []
    for s in np.arange(0, n_ + 1e-9, step):
        c = a_ + s * t
        p = peak(samp(c[0] + offs * nrm[0], c[1] + offs * nrm[1]))
        if p is not None:
            out.append(c + (offs[0] + p * (offs[1] - offs[0])) * nrm)
    return np.array(out)


def tls(pts):
    c = pts.mean(0)
    t = np.linalg.svd(pts - c)[2][0]
    return c, t, np.array([-t[1], t[0]])


def line(name, a_, b_, note, ends=None, max_gap=0.15):
    pts = ridge(a_, b_)
    m = np.ones(len(pts), bool)
    for _ in range(4):
        c, t, n_ = tls(pts[m])
        r = (pts - c) @ n_
        m = np.abs(r) < max(2.5 * float(np.std(r[m])), 0.004)
    # longest run of inliers within 2.7 m, gaps < 0.15 units
    c, t, n_ = tls(pts[m])
    if t @ (np.array(b_) - np.array(a_)) < 0:
        t, n_ = -t, -n_
    s = (pts - c) @ t
    ok = np.abs((pts - c) @ n_) < 0.012
    o = np.argsort(s)
    runs, cur = [], []
    for i in o:
        if not ok[i]:
            continue
        if cur and s[i] - s[cur[-1]] > max_gap:
            runs.append(cur)
            cur = []
        cur.append(i)
    runs.append(cur)
    run = np.array(max(runs, key=lambda r_: s[r_[-1]] - s[r_[0]] if r_ else -1))
    c, t, n_ = tls(pts[run])
    if t @ (np.array(b_) - np.array(a_)) < 0:
        t, n_ = -t, -n_
    s = (pts[run] - c) @ t
    r = (pts[run] - c) @ n_
    p0, p1 = c + s.min() * t, c + s.max() * t
    length = float(s.max() - s.min())
    sig_off = float(np.std(r) / math.sqrt(len(r)))
    sig_ang = float(np.std(r) / math.sqrt(((s - s.mean()) ** 2).sum()))
    item = {
        "name": name, "note": note,
        "from": [round(float(x), 4) for x in p0], "to": [round(float(x), 4) for x in p1],
        "from_world": world(p0), "to_world": world(p1),
        "length_m": round(length * EDGE, 1),
        "bearing_deg": round(math.degrees(math.atan2(t[0], -t[1])) % 360, 3),
        "fit": {"samples": int(len(run)), "rms_m": round(float(np.sqrt((r ** 2).mean())) * EDGE, 2),
                "offset_sigma_m": round(sig_off * EDGE, 2), "angle_sigma_deg": round(math.degrees(sig_ang), 3)},
        "abs_m": 6.1, "angle_abs_deg": round(math.degrees(math.atan2(6.1 * math.sqrt(2), length * EDGE)), 2),
    }
    LINES[name] = (c, t, n_)
    if ends:
        item["ends_on_rings"] = ends
    return item


def ring_fit(c0, r_lo, r_hi, n=144):
    c0 = np.array(c0, float)
    rr = np.linspace(r_lo, r_hi, 61)
    pts = []
    for ang in np.linspace(0, 2 * math.pi, n, endpoint=False):
        uu, vv = c0[0] + rr * math.cos(ang), c0[1] + rr * math.sin(ang)
        p = peak(samp(uu, vv))
        if p is not None:
            k = min(int(p), 59)
            f = p - k
            pts.append([uu[k] + f * (uu[k + 1] - uu[k]), vv[k] + f * (vv[k + 1] - vv[k])])
    pts = np.array(pts)
    m = np.ones(len(pts), bool)
    for _ in range(5):
        A = np.c_[2 * pts[m], np.ones(m.sum())]
        x = np.linalg.lstsq(A, (pts[m] ** 2).sum(1), rcond=None)[0]
        c = x[:2]
        r = math.sqrt(x[2] + c @ c)
        res = np.hypot(*(pts - c).T) - r
        m = np.abs(res) < max(2.5 * float(np.std(res[m])), 0.006)
    sd = float(np.std(res[m]))
    return c, r, sd, int(m.sum()), sd * math.sqrt(2 / m.sum())


def off_m(name, p):
    c, t, n_ = LINES[name]
    return round(float((np.array(p) - c) @ n_) * EDGE, 2)


LINES: dict = {}
RINGS = {}
for k in sorted((k for k in G if k != "gate"), key=int):
    c, r, sd, nn, sc = ring_fit(G[k], 0.36, 0.48)
    RINGS[int(k)] = {"centre": [round(float(x), 4) for x in c], "centre_world": world(c), "r_m": round(r * EDGE, 1),
                     "from_canon_m": round(float(np.linalg.norm(c - G[k])) * EDGE, 1),
                     "fit": {"samples": nn, "rms_m": round(sd * EDGE, 1), "centre_sigma_m": round(sc * EDGE, 1)}}
RC = {k: np.array(v["centre"]) for k, v in RINGS.items()}

items = [
    line("axis_north", (0.0, -4.9), (0.0, -0.45), "gate to Silo 1's ring path; no path crosses Silo 1's north berm",
         ["gate", 1]),
    line("axis_south", (0.0, 0.45), (0.0, 2.2), "Silo 1's ring path (south, past the bare apron) to Silo 2's ring path",
         [1, 2]),
    line("founders_west", (-0.45, 0.0), (-2.95, 0.0), "Silo 1's ring path due west to Silo 42's ring path", [1, 42]),
    line("founders_east", (0.45, -0.03), (2.95, -0.09), "Silo 1's ring path east to Silo 25's ring path; meets 25's "
         "circle north of the centre line", [1, 25]),
    line("north_cross", (-1.6, -3.08), (1.5, -3.08), "cross path north of the 44 and 17 rings; joins the axis by two "
         "fillets (a Y on each side, about 0.1 units long); curves at its ends to 44/45 and 16/17; the Y junction "
         "leaves a gap at the axis, bridged here", max_gap=0.4),
]
# the axis as one line: both halves together
ax = np.r_[ridge((0.0, -4.9), (0.0, -0.45)), ridge((0.0, 0.45), (0.0, 2.2))]
m = np.ones(len(ax), bool)
for _ in range(4):
    c, t, n_ = tls(ax[m])
    r = (ax - c) @ n_
    m = np.abs(r) < max(2.5 * float(np.std(r[m])), 0.004)
c, t, n_ = tls(ax[m])
LINES["axis"] = (c, t, n_)
r = (ax[m] - c) @ n_
axis = {
    "bearing_deg": round(math.degrees(math.atan2(t[0], -t[1])) % 180, 3),
    "u_at_v0": round(float(c[0] - c[1] * t[0] / t[1]), 4),
    "rms_m": round(float(np.sqrt((r ** 2).mean())) * EDGE, 2),
    "north_vs_south_half": {
        "bearing_diff_deg": round(abs((items[0]["bearing_deg"] - items[1]["bearing_deg"] + 90) % 180 - 90), 3),
        "offset_at_silo1_m": round(off_m("axis_south", RC[1]) - off_m("axis_north", RC[1]), 2)},
    "offset_of_ring_centre_m": {str(k): off_m("axis", RC[k]) for k in (1, 2)},
    "offset_of_canon_point_m": {k: off_m("axis", G[k]) for k in ("1", "2", "gate")},
    "note": "one straight line: gate, Silo 1's centre and Silo 2's centre within a few metres. The halves are measured separately (axis_north, axis_south).",
}
for it in items:
    if it["name"].startswith("founders"):
        it["offset_of_silo1_centre_m"] = off_m(it["name"], RC[1])
        it["v_at_u0"] = round(float(LINES[it["name"]][0][1] - LINES[it["name"]][0][0] * LINES[it["name"]][1][1] / LINES[it["name"]][1][0]), 4)
items[4]["v_at_u0"] = round(float(LINES["north_cross"][0][1] - LINES["north_cross"][0][0] * LINES["north_cross"][1][1] / LINES["north_cross"][1][0]), 4)
items[4]["angle_to_axis_deg"] = round(math.degrees(math.acos(abs(float(LINES["north_cross"][1] @ LINES["axis"][1])))), 2)

# rosettes: positions by eye on the rectified frame, refined here; kind read from the zoomed frame
ROS = [((-1.75, -0.95), "concentric"), ((-1.65, 0.95), "plain (one circle, faint inner ring)"),
       ((-2.67, 1.45), "concentric (faint)"), ((-1.83, 2.10), "concentric"), ((1.75, 2.01), "concentric"),
       ((2.60, 1.45), "circle with trees inside"), ((1.81, -1.21), "dark disc (trees), circle faint"),
       ((2.21, -2.05), "dark disc (trees), circle faint"), ((-4.02, 0.14), "circle with trees inside")]
ros = []
for (u0, v0), kind in ROS:
    c, r, sd, nn, sc = ring_fit((u0, v0), 0.08, 0.22)
    # concentric rings: mean radial profile
    rr = np.linspace(0.0, r + 0.02, 120)
    prof = np.zeros_like(rr)
    for ang in np.linspace(0, 2 * math.pi, 72, endpoint=False):
        prof += samp(c[0] + rr * math.cos(ang), c[1] + rr * math.sin(ang))
    prof /= 72
    sm = np.convolve(prof, np.ones(3) / 3, "same")
    # a ring: local maximum standing 1.5 above the lowest value within +-6 m
    w = max(2, int(6 / EDGE / (rr[1] - rr[0])))
    pk = [i for i in range(1, len(sm) - 1) if sm[i] > sm[i - 1] and sm[i] >= sm[i + 1]
          and sm[i] - sm[max(0, i - w):i + w + 1].min() > 1.5]
    tri = sorted(RC, key=lambda k: np.linalg.norm(RC[k] - c))[:3]
    ros.append({"centre": [round(float(x), 4) for x in c], "centre_world": world(c), "kind": kind,
                "outer_r_m": round(r * EDGE, 1), "ring_radii_m_angle_mean": [round(float(rr[i]) * EDGE, 1) for i in pk],
                "between": tri,
                "from_triangle_centroid_m": round(float(np.linalg.norm(c - np.mean([RC[k] for k in tri], 0))) * EDGE, 1),
                "fit": {"samples": nn, "rms_m": round(sd * EDGE, 1), "centre_sigma_m": round(sc * EDGE, 1)}})

# links: neighbouring rings whose circles nearly touch; is there a straight pale connector across the gap?
links = []
ks = sorted(RC)
for i in ks:
    for j in ks:
        if i >= j:
            continue
        d = float(np.linalg.norm(RC[j] - RC[i]))
        if d > 1.15:
            continue
        ri, rj = RINGS[i]["r_m"] / EDGE, RINGS[j]["r_m"] / EDGE
        gap = d - ri - rj
        e = (RC[j] - RC[i]) / d
        if gap < 0.02:
            links.append({"rings": [i, j], "gap_m": round(gap * EDGE, 1), "kind": "circles touch or overlap"})
            continue
        a_, b_ = RC[i] + e * (ri + 0.01), RC[j] - e * (rj + 0.01)
        pts = ridge(a_, b_, half=0.03, step=0.004)
        if len(pts) == 0:
            cov, offm = 0.0, None
        else:
            nn_ = np.array([-e[1], e[0]])
            offs = (pts - a_) @ nn_
            med = float(np.median(offs))
            cov = float((np.abs(offs - med) < 0.006).sum() * 0.004 / max(gap - 0.02, 0.004))
            offm = round(med * EDGE, 1)
        links.append({"rings": [i, j], "gap_m": round(gap * EDGE, 1),
                      "kind": "straight connector" if cov > 0.7 else "no straight connector on the centre line",
                      "coverage": round(min(cov, 1.0), 2), "offset_from_centre_line_m": offm})

for it in items:
    if "ends_on_rings" in it:
        gaps = []
        for end, k in zip(("from", "to"), it["ends_on_rings"]):
            if k == "gate":
                gaps.append(round(float(np.linalg.norm(np.array(it[end]) - G["gate"])) * EDGE, 1))
            else:
                gaps.append(round((float(np.linalg.norm(np.array(it[end]) - RC[k])) - RINGS[k]["r_m"] / EDGE) * EDGE, 1))
        it["end_gap_to_ring_path_m"] = gaps
items[0]["note"] += ("; the same line's samples go on to v -4.905 (gate canopy at -4.99) past a gap at v -4.9 to -4.3, "
                     "where the stream of visitors covers the path")
items[2]["note"] += "; it ends where it bends onto the ring circle (end_gap_to_ring_path_m)"
items[3]["note"] += "; it ends where it bends onto the ring circle (end_gap_to_ring_path_m)"


def vs_line(name, p, q):
    """Signed metres from the measured line to the planned segment's ends p, q (canon units)."""
    return [off_m(name, p), off_m(name, q)]


# the build's rules (paths.plan at 1f74002) in canon units, ring path r 110 m: where they put each line against the frame
RP = 110 / EDGE
build = {
    "axis_north (Silo 1 fit point toward the gate fit point)": vs_line("axis", G["1"] + np.array([0, -RP]), G["gate"]),
    "axis_south (same line south to Silo 2's circle)": vs_line("axis", G["1"] + np.array([0, RP]),
                                                                np.array([0.0, G["2"][1] - RP])),
    "founders_west (centre line Silo 1 -> 42, at the two circles)": vs_line(
        "founders_west", G["1"] + RP * (G["42"] - G["1"]) / np.linalg.norm(G["42"] - G["1"]),
        G["42"] - RP * (G["42"] - G["1"]) / np.linalg.norm(G["42"] - G["1"])),
    "founders_east (centre line Silo 1 -> 25, at the two circles)": vs_line(
        "founders_east", G["1"] + RP * (G["25"] - G["1"]) / np.linalg.norm(G["25"] - G["1"]),
        G["25"] - RP * (G["25"] - G["1"]) / np.linalg.norm(G["25"] - G["1"])),
    "north_cross (40 m beyond the farther of the 44/17 circles), at u -1 and +1": vs_line(
        "north_cross", np.array([-1.0, min(G["44"][1], G["17"][1]) - RP - 40 / EDGE]),
        np.array([1.0, min(G["44"][1], G["17"][1]) - RP - 40 / EDGE])),
}


def positive_is(name):
    n_ = LINES[name][2]
    return ("south" if n_[1] > 0 else "north") if abs(n_[1]) > abs(n_[0]) else ("east" if n_[0] > 0 else "west")


build = {k: {"offset_m": v, "positive_is": positive_is(k.split(" ")[0] if not k.startswith("axis") else "axis")}
         for k, v in build.items()}
for it in items:
    it["offsets_positive_is"] = positive_is(it["name"])
axis["offsets_positive_is"] = positive_is("axis")

out = {
    "build_vs_frame": build,
    "about": "Straight paths, ring circles and rosettes measured on the S3 2052 aerial (aerial2052-1920.jpg, branch "
             "silo-canon-img) through canon/fit.json Hf1920, by tools/silo/canon_lines.py. Canon units: Silo 1's fit "
             "point at 0,0, flower edge 1, x east, y south, gate north. World: Silo 1 %s, rotation %g, spacing %g. "
             "Errors: fit = the ridge's scatter (statistical), abs_m = the homography's absolute error (6.1 m rms "
             "of 50 measured ring centres against the canon ground after a similarity; 12.2 m max). Straightness and "
             "line-through-centre need no absolute accuracy: a homography keeps lines straight." % (list(ONE), ROT, EDGE),
    "axis": axis, "lines": items, "rosettes": ros, "rings": RINGS, "links": links,
    "not_straight": ["Silo 1 to 30 and Silo 1 to 10: curves from Silo 1's south ring path (S-bends), not lines",
                     "most other paths between rings are arcs tangent to the ring circles"],
}
json.dump(out, open(os.path.join(HERE, "canon", "lines.json"), "w"), indent=1)
print(json.dumps(axis, indent=1))
for it in items:
    print(it["name"], it["from"], "->", it["to"], it["length_m"], "m bearing", it["bearing_deg"], it["fit"],
          {k: it[k] for k in it if k in ("offset_of_silo1_centre_m", "v_at_u0", "angle_to_axis_deg")})
for rz in ros:
    print("rosette", rz["centre"], rz["kind"], rz["outer_r_m"], rz["ring_radii_m_angle_mean"], rz["between"], rz["fit"])
print("links:", sum(l_["kind"] == "straight connector" for l_ in links), "straight of", len(links))

if a.png:
    o = im.copy()
    for it in items:
        p0, p1 = P(np.array([it["from"][0]]), np.array([it["from"][1]])), P(np.array([it["to"][0]]), np.array([it["to"][1]]))
        cv2.line(o, (int(p0[0][0]), int(p0[1][0])), (int(p1[0][0]), int(p1[1][0])), (0, 0, 255), 1)
    for k, v in RINGS.items():
        c = v["centre"]
        x, y = P(np.array([c[0]]), np.array([c[1]]))
        cv2.circle(o, (int(x[0]), int(y[0])), 2, (255, 0, 255), -1)
    for rz in ros:
        c = rz["centre"]
        pts = np.array([P(np.array([c[0] + rz["outer_r_m"] / EDGE * math.cos(t_)]),
                          np.array([c[1] + rz["outer_r_m"] / EDGE * math.sin(t_)])) for t_ in np.linspace(0, 6.3, 40)])
        cv2.polylines(o, [pts.reshape(-1, 2).astype(np.int32)], True, (0, 255, 255), 1)
    cv2.imwrite(a.png, o)
