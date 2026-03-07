"""
src/stand.py — Triangle stand SVG generator (D-18 + D-19).

D-18/D-19: Solid right-triangle side pieces + 6 cross members.
Parts (8 total):
  stand_L            — right triangle 240×420mm with 5 edge notches + 1 hyp notch (L-shaped upright notches)
  stand_R            — mirror of stand_L
  stand_rear_cross_1 — 374×30mm with stile slots (at upright y=60)
  stand_rear_cross_2 — 374×30mm plain (at upright y=210)
  stand_rear_cross_3 — 374×30mm with stile slots (at upright y=360)
  stand_base_cross_1 — 374×30mm plain (at base x=80)
  stand_base_cross_2 — 374×30mm plain (at base x=160)
  hyp_cross          — 374×30mm plain (at hyp t=0.25; placed rotated 90° on sheet)

Assembly: upright/base cross members slide into L-shaped edge notches and drop 2mm (gravity).
Hyp cross member slides into parallelogram notch on hypotenuse edge.
Loom stiles drop into stile slots of rear_cross_1 and rear_cross_3.

Usage:
  python3 -m src.stand           → writes output/optional_loom_stand.svg
  from src.stand import generate → returns SVG string
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT, make_params
from src.geometry import (
    bounding_box, bboxes_overlap, mirror_x, place,
    pts_to_path, cut_path, etch_text, svg_open, svg_close, svg_group,
    rect_pts,
    triangle_pts,
    hole_to_path,
)

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "optional_loom_stand.svg"
)


# ---------------------------------------------------------------------------
# Part builders — return (local_pts, local_holes)
# ---------------------------------------------------------------------------

def _hyp_notch_pts(p: dict) -> list:
    """
    Compute the 4 parallelogram points for the hypotenuse edge notch (D-19).

    Hyp runs from (base_l, upright_h) toward (0, 0) in the path traversal.
    Notch centre at (STAND_HYP_CX, STAND_HYP_CY) = (60, 105) at t=0.25 from top vertex.
    Returns [P_before, P_before_inner, P_after_inner, P_after] in path order.
    """
    base_l    = p["STAND_BASE_L"]
    upright_h = p["STAND_UPRIGHT_H"]
    cx        = p["STAND_HYP_CX"]
    cy        = p["STAND_HYP_CY"]
    notch_w   = p["STAND_NOTCH_W"]
    notch_d   = p["STAND_NOTCH_D"]

    hyp_len = math.hypot(base_l, upright_h)   # ≈ 483.74mm

    # Tangent in path direction: from (base_l, upright_h) toward (0, 0)
    tx = -base_l    / hyp_len   # ≈ -0.4961
    ty = -upright_h / hyp_len   # ≈ -0.8682

    # Inward normal (right of path direction for CW winding): rotate tangent by -90°
    nx = ty    # ≈ -0.8682
    ny = -tx   # ≈  0.4961

    half_w = notch_w / 2.0   # = 15.05mm

    # P_before: on hyp, before centre in path direction (= centre minus tangent × half_w)
    pbx = cx - half_w * tx
    pby = cy - half_w * ty
    # P_before_inner: P_before + depth × inward_normal
    pbix = pbx + notch_d * nx
    pbiy = pby + notch_d * ny
    # P_after: on hyp, after centre
    pax = cx + half_w * tx
    pay = cy + half_w * ty
    # P_after_inner: P_after + depth × inward_normal
    paix = pax + notch_d * nx
    paiy = pay + notch_d * ny

    return [(pbx, pby), (pbix, pbiy), (paix, paiy), (pax, pay)]


def build_stand_triangle(p: dict):
    """
    Solid right-triangle side piece (D-18 + D-19).
    Vertices: (0,0) top-back, (0,upright_h) bottom-back (right angle),
              (base_l, upright_h) bottom-front.
    3 upright notches (L-shaped, D-19) at STAND_MORT_Y_TOP/MID/BOT.
    2 base notches (plain) at STAND_BASE_NOTCH_X1/X2.
    1 hyp notch (parallelogram, D-19) at STAND_HYP_CX/CY.
    """
    upright_notch_ys = [
        p["STAND_MORT_Y_TOP"],
        p["STAND_MORT_Y_MID"],
        p["STAND_MORT_Y_BOT"],
    ]
    base_notch_xs = [
        p["STAND_BASE_NOTCH_X1"],
        p["STAND_BASE_NOTCH_X2"],
    ]
    pts = triangle_pts(
        p["STAND_UPRIGHT_H"], p["STAND_BASE_L"],
        upright_notch_ys, base_notch_xs,
        p["STAND_NOTCH_W"], p["STAND_NOTCH_D"],
        notch_entry=p["STAND_NOTCH_ENTRY"],
        notch_entry_d=p["STAND_NOTCH_ENTRY_D"],
        hyp_notch_pts=_hyp_notch_pts(p),
    )
    return pts, []


def build_stand_cross(p: dict, with_stile_slots: bool = False):
    """
    Cross member: (STAND_SPREAD_L + 2×STAND_SPREAD_TEN_L) × STAND_SPREAD_W.
    If with_stile_slots: two concave stile slots in top edge (y=0), each
    STAND_STILE_SLOT_W × STAND_STILE_SLOT_D, flush with the tenon ends.
    """
    total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]
    w = p["STAND_SPREAD_W"]

    if not with_stile_slots:
        return rect_pts(0.0, 0.0, total_l, w), []

    sw = p["STAND_STILE_SLOT_W"]
    sd = p["STAND_STILE_SLOT_D"]
    ten_l = p["STAND_SPREAD_TEN_L"]

    # Slot centres: left slot flush-left with body start, right flush-right with body end
    cx1 = ten_l + sw / 2.0
    cx2 = total_l - ten_l - sw / 2.0

    pts = [(0.0, 0.0)]
    for cx in (cx1, cx2):
        x0 = cx - sw / 2.0
        x1 = cx + sw / 2.0
        pts.append((x0, 0.0))
        pts.append((x0, sd))
        pts.append((x1, sd))
        pts.append((x1, 0.0))
    pts.append((total_l, 0.0))
    pts.append((total_l, w))
    pts.append((0.0, w))

    return pts, []


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout(p: dict) -> list:
    """
    Place all 7 parts on the 600×600mm 6mm ply sheet.

    Layout (all mm, origin top-left, M=2mm margin, G=2mm gap):
      stand_L          at (M, M)              — 240×420mm
      stand_R          at (M+240+G, M)        — 240×420mm (mirror of L)
      hyp_cross        at (M+240+G+240+G, M)  — 30×374mm (rotated 90°, right of triangles)
      stand_rear_cross_1 at (M, M+420+G)      — 374×30mm (with stile slots)
      stand_rear_cross_2 at (M, +G)           — 374×30mm
      stand_rear_cross_3 at (M, +G)           — 374×30mm (with stile slots)
      stand_base_cross_1 at (M, +G)           — 374×30mm
      stand_base_cross_2 at (M, +G)           — 374×30mm

    6 cross members total (D-19): 5 horizontal + 1 rotated (hyp_cross).
    Returns list of dicts: {id, label, sheet_pts, sheet_holes, bbox}.
    Raises ValueError if any part exceeds sheet bounds or parts overlap.
    """
    M = p["MARGIN"]
    G = 2.0

    tri_pts, tri_holes = build_stand_triangle(p)
    tri_bb = bounding_box(tri_pts)
    tri_w = tri_bb[2] - tri_bb[0]   # = STAND_BASE_L = 240mm
    tri_h = tri_bb[3] - tri_bb[1]   # = STAND_UPRIGHT_H = 420mm

    # Mirror stand_L about its own centre x to get stand_R
    cx = tri_w / 2.0
    tri_pts_r = mirror_x(tri_pts, cx)

    cross_plain_pts, _ = build_stand_cross(p, with_stile_slots=False)
    cross_slot_pts, _ = build_stand_cross(p, with_stile_slots=True)
    cross_h = p["STAND_SPREAD_W"]   # = 30mm
    total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]  # = 374mm

    # hyp_cross placed rotated 90° (30mm wide × 374mm tall on sheet)
    cross_rotated_pts = rect_pts(0.0, 0.0, cross_h, total_l)

    y_cross = M + tri_h + G
    x_hyp = M + tri_w + G + tri_w + G   # = 2 + 240 + 2 + 240 + 2 = 486mm

    parts_local = [
        ("stand_L",            tri_pts,        tri_holes, "STAND L",   M,       M),
        ("stand_R",            tri_pts_r,      tri_holes, "STAND R",   M+tri_w+G, M),
        ("hyp_cross",          cross_rotated_pts, [],     "HYP X",     x_hyp,   M),
        ("stand_rear_cross_1", cross_slot_pts,  [],       "REAR X1",   M,       y_cross),
        ("stand_rear_cross_2", cross_plain_pts, [],       "REAR X2",   M,       y_cross + (cross_h + G)),
        ("stand_rear_cross_3", cross_slot_pts,  [],       "REAR X3",   M,       y_cross + 2 * (cross_h + G)),
        ("stand_base_cross_1", cross_plain_pts, [],       "BASE X1",   M,       y_cross + 3 * (cross_h + G)),
        ("stand_base_cross_2", cross_plain_pts, [],       "BASE X2",   M,       y_cross + 4 * (cross_h + G)),
    ]

    placed = []
    for pid, local_pts, local_holes, label, sx, sy in parts_local:
        sheet_pts, sheet_holes = place(local_pts, local_holes, sx, sy)
        bb = bounding_box(sheet_pts)
        placed.append({
            "id":          pid,
            "label":       label,
            "sheet_pts":   sheet_pts,
            "sheet_holes": sheet_holes,
            "bbox":        bb,
        })

    # Validate sheet bounds
    sw, sh = p["SHEET_W"], p["SHEET_H"]
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        if x0 < M - 1e-6 or y0 < M - 1e-6 or x1 > sw - M + 1e-6 or y1 > sh - M + 1e-6:
            raise ValueError(
                f"Part '{part['id']}' exceeds sheet bounds: "
                f"bbox=({x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}) "
                f"sheet=({M},{M},{sw-M},{sh-M})"
            )

    return placed


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render(placed: list, p: dict) -> str:
    """Render placed parts to SVG string."""
    sw, sh = p["SHEET_W"], p["SHEET_H"]
    parts = []
    for part in placed:
        outer = cut_path(pts_to_path(part["sheet_pts"]))
        holes = [cut_path(hole_to_path(h)) for h in part["sheet_holes"]]
        label = etch_text(
            part["bbox"][0] + 1.0,
            part["bbox"][1] + 4.0,
            part["label"],
        )
        parts.append(svg_group(part["id"], [outer] + holes + [label]))

    return svg_open(sw, sh) + "\n".join(parts) + svg_close()


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def verify(placed: list, p: dict) -> list:
    """
    Run layout invariants I-1, I-2, I-12 against the placed parts.
    Returns list of (name, ok, detail).
    """
    import re as _re
    results = []
    M = p["MARGIN"]
    sw, sh = p["SHEET_W"], p["SHEET_H"]

    # I-1: all parts within sheet bounds
    oob = []
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        if x0 < M - 1e-6 or y0 < M - 1e-6 or x1 > sw - M + 1e-6 or y1 > sh - M + 1e-6:
            oob.append(f"{part['id']}:({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f})")
    ok_i1 = len(oob) == 0
    results.append(("I-1", ok_i1,
        "all within bounds" if ok_i1 else f"OOB: {'; '.join(oob)}"))

    # I-2: no overlaps
    overlaps = []
    for i, a in enumerate(placed):
        for j, b in enumerate(placed):
            if j <= i:
                continue
            if bboxes_overlap(a["bbox"], b["bbox"]):
                overlaps.append(f"{a['id']} vs {b['id']}")
    ok_i2 = len(overlaps) == 0
    results.append(("I-2", ok_i2,
        "no overlaps" if ok_i2 else f"Overlaps: {'; '.join(overlaps)}"))

    # I-12: all cut paths closed
    svg = render(placed, p)
    paths = _re.findall(r' d="([^"]+)"', svg)
    open_paths = [d[:40] for d in paths if not d.rstrip().endswith("Z")]
    ok_i12 = len(open_paths) == 0
    results.append(("I-12", ok_i12,
        f"all {len(paths)} paths closed" if ok_i12
        else f"{len(open_paths)} open: {open_paths[:3]}"))

    return results


# ---------------------------------------------------------------------------
# Generate / write
# ---------------------------------------------------------------------------

def generate(p: dict = None) -> str:
    """Generate stand SVG string. Does not write to disk."""
    if p is None:
        p = DEFAULT
    placed = layout(p)
    return render(placed, p)


def write(p: dict = None, path: str = None) -> str:
    """Generate stand SVG, verify, write to disk. Returns file path."""
    if p is None:
        p = DEFAULT
    if path is None:
        path = OUTPUT_PATH

    placed = layout(p)
    results = verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    if failures:
        msg = "\n".join(f"  {n}: {d}" for n, d in failures)
        raise ValueError(f"Stand layout verification failed:\n{msg}")

    svg = render(placed, p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


if __name__ == "__main__":
    path = write()
    print(f"Written: {path}")
    placed = layout(DEFAULT)
    for part in placed:
        bb = part["bbox"]
        print(f"  {part['id']:22s}  x={bb[0]:.1f}–{bb[2]:.1f}  y={bb[1]:.1f}–{bb[3]:.1f}"
              f"  ({bb[2]-bb[0]:.1f}×{bb[3]-bb[1]:.1f}mm)")
