"""
src/box.py — Box SVG generator.

Generates output/box.svg: all box panels on a single 600×600mm 3mm ply sheet.
Stand pieces are NOT included here — see src/stand.py → output/optional_loom_stand.svg (D-16).

Parts:
  Box (6 panels, press-fit assembly):
    - box_base:              BOX_OUTER_L × BOX_OUTER_W (floor panel, edge notches)
    - box_lid:               BOX_INTERIOR_L × BOX_INTERIOR_W (slides through short-wall dado)
    - box_long_wall_L/R:     BOX_OUTER_L × BOX_INTERIOR_H (×2, corner sockets + base tabs)
    - box_short_wall_front/back: BOX_OUTER_W × BOX_INTERIOR_H (×2, corner tabs + dado slot)

Assembly: connect 4 walls at corners → lower base onto wall bottom tabs → slide lid in.

Usage:
  python3 -m src.box            → writes output/box.svg, prints report
  from src.box import generate  → returns SVG string
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT, make_params
from src.geometry import (
    bounding_box, bboxes_overlap, translate, mirror_x, place,
    pts_to_path, cut_path, etch_text, svg_open, svg_close, svg_group,
    rect_pts,
    rect_hole, hole_to_path,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "optional_box.svg")


# ---------------------------------------------------------------------------
# Part builders — return (local_pts, local_holes)
# ---------------------------------------------------------------------------

def build_box_base(p: dict):
    """
    Floor panel: BOX_OUTER_L × BOX_OUTER_W with edge notches for wall bottom tabs.
    Notches are concave (go inward from edge) — bbox unchanged.
    Front/back edges: BOX_BASE_NTABS_L notches at L*i/(n+1) for i=1..n.
    Left/right edges: BOX_BASE_NTABS_S notches centred on interior (MAT3 + INTERIOR_W/2).
    """
    L   = p["BOX_OUTER_L"]
    W   = p["BOX_OUTER_W"]
    nd  = p["MAT3"]                   # notch depth (inward)
    tw2 = p["BOX_TAB_W"] / 2.0        # half notch width
    nl  = p["BOX_BASE_NTABS_L"]
    ns  = p["BOX_BASE_NTABS_S"]

    tx = [L * i / (nl + 1) for i in range(1, nl + 1)]
    ty = [p["MAT3"] + p["BOX_INTERIOR_W"] * i / (ns + 1) for i in range(1, ns + 1)]

    # Front edge (y=0, left→right): notches step to y=+nd (inward)
    front = [(0.0, 0.0)]
    for cx in tx:
        front += [(cx - tw2, 0.0), (cx - tw2, nd), (cx + tw2, nd), (cx + tw2, 0.0)]
    front.append((L, 0.0))

    # Right edge (x=L, top→bottom): notches step to x=L-nd (inward)
    right = []
    for cy in ty:
        right += [(L, cy - tw2), (L - nd, cy - tw2), (L - nd, cy + tw2), (L, cy + tw2)]
    right.append((L, W))

    # Back edge (y=W, right→left): notches step to y=W-nd (inward), reversed order
    back = []
    for cx in reversed(tx):
        back += [(cx + tw2, W), (cx + tw2, W - nd), (cx - tw2, W - nd), (cx - tw2, W)]
    back.append((0.0, W))

    # Left edge (x=0, bottom→top): notches step to x=+nd (inward), reversed order
    left = []
    for cy in reversed(ty):
        left += [(0.0, cy + tw2), (nd, cy + tw2), (nd, cy - tw2), (0.0, cy - tw2)]
    # Z closes (last pt) back to (0,0)

    return front + right + back + left, []


def build_box_lid(p: dict):
    """Lid panel: BOX_INTERIOR_L × BOX_INTERIOR_W (rests on top of box walls)."""
    pts = rect_pts(0.0, 0.0, p["BOX_INTERIOR_L"], p["BOX_INTERIOR_W"])
    return pts, []


def build_box_long_wall(p: dict):
    """
    Long wall: placed in portrait on sheet.
    Local coords: BOX_INTERIOR_H wide (x) × BOX_OUTER_L tall (y).
    N=1 corner socket at each end: MAT3 deep × BOX_TAB_W wide, centred on width.
    Socket is concave — does not change bounding box.
    """
    l   = p["BOX_OUTER_L"]       # 466mm — long axis (y in portrait)
    h   = p["BOX_INTERIOR_H"]    # 12mm — short axis (x in portrait)
    t   = p["MAT3"]              # 3mm socket depth (y direction)
    tw  = p["BOX_TAB_W"]         # 4mm socket width (x direction)
    sx  = (h - tw) / 2.0         # 4mm — socket left x (centred on h=12)
    ex  = sx + tw                 # 8mm — socket right x
    # Bottom tabs on the right edge (x=h, the "base" side in assembly)
    d    = p["MAT3"]              # tab protrusion = 3mm
    n    = p["BOX_BASE_NTABS_L"]  # = 3
    tw2  = p["BOX_TAB_W"] / 2.0   # half-tab-width = 2mm
    right_edge = [(h, 0.0)]
    for i in range(1, n + 1):
        cy = l * i / (n + 1)
        right_edge += [
            (h,   cy - tw2), (h+d, cy - tw2),   # tab: step out
            (h+d, cy + tw2), (h,   cy + tw2),   # tab: step back
        ]
    right_edge.append((h, l))

    pts = [
        (0.0, 0.0),
        (sx,  0.0), (sx, t), (ex, t), (ex, 0.0),   # top socket
        *right_edge,                                  # right edge with base tabs
        (ex,  l), (ex, l-t), (sx, l-t), (sx, l),   # bottom socket
        (0.0, l),
        # Z closes to (0.0, 0.0)
    ]
    return pts, []


def build_box_short_wall(p: dict):
    """
    Short wall: BOX_INTERIOR_W body, BOX_INTERIOR_H tall.
    N=1 corner tabs at each side: MAT3 protrusion × BOX_TAB_W tall, centred on height.
      → total bounding box width = BOX_INTERIOR_W + 2×MAT3 = BOX_OUTER_W.
    Top slot (BOX_DADO_W deep, full width): allows lid to slide through.
      → bounding box top at y=BOX_DADO_W (slot is open at y=0).
    """
    w   = p["BOX_INTERIOR_W"]    # 258mm body width
    h   = p["BOX_INTERIOR_H"]    # 12mm total height
    t   = p["MAT3"]              # 3mm tab protrusion
    tw  = p["BOX_TAB_W"]         # 4mm tab height
    dw  = p["BOX_DADO_W"]        # 3.2mm lid slot depth (from top)
    sy  = (h - tw) / 2.0         # 4mm — tab top y (centred on 12mm)
    ey  = sy + tw                 # 8mm — tab bottom y
    # Bottom tabs on the bottom edge (y=h, the base side in assembly)
    d_b  = p["MAT3"]              # tab protrusion = 3mm
    n_b  = p["BOX_BASE_NTABS_S"]  # = 1
    tw2b = p["BOX_TAB_W"] / 2.0   # 2mm
    bot_edge = [(0.0, h)]
    for i in range(1, n_b + 1):
        cx = w * i / (n_b + 1)
        bot_edge += [
            (cx - tw2b, h),       (cx - tw2b, h + d_b),   # tab: step down
            (cx + tw2b, h + d_b), (cx + tw2b, h),          # tab: step back
        ]
    bot_edge.append((w, h))

    pts = [
        (0.0, dw),
        (0.0, sy), (-t, sy), (-t, ey), (0.0, ey),   # left tab
        *bot_edge,                                     # bottom edge with base tab
        (w, ey), (w+t, ey), (w+t, sy), (w, sy),      # right tab
        (w, dw),
        # Z closes to (0.0, dw)
    ]
    return pts, []


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout(p: dict) -> list:
    """
    Place all 6 box parts on the 600×600mm 3mm ply sheet.

    Returns list of dicts: { 'id', 'label', 'sheet_pts', 'sheet_holes', 'bbox' }
    Raises ValueError if any part exceeds sheet bounds or parts overlap.

    Sheet layout (all measurements in mm, origin top-left):
      Column A (x=M):        base, lid stacked vertically; short walls + spreader in bottom strip
      Column B (x=M+base_l+G): two long walls in portrait orientation
    """
    M  = p["MARGIN"]   # = 2mm
    G  = 2.0           # inter-part gap

    parts_local = [
        ("box_base",             *build_box_base(p),      "BOX BASE"),
        ("box_lid",              *build_box_lid(p),       "BOX LID"),
        ("box_long_wall_L",      *build_box_long_wall(p), "LONG WALL L"),
        ("box_long_wall_R",      *build_box_long_wall(p), "LONG WALL R"),
        ("box_short_wall_front", *build_box_short_wall(p), "SHORT WALL FR"),
        ("box_short_wall_back",  *build_box_short_wall(p), "SHORT WALL BK"),
    ]

    # ── Sheet positions ────────────────────────────────────────────────────
    base_l    = p["BOX_OUTER_L"]                         # 466mm
    base_w    = p["BOX_OUTER_W"]                         # 264mm
    lid_w     = p["BOX_INTERIOR_W"]                      # 258mm
    wall_pw   = p["BOX_INTERIOR_H"] + p["MAT3"]          # 15mm (long wall portrait width)
    sw_bbox_w = p["BOX_OUTER_W"]                         # 264mm (short wall incl. corner tabs)
    sw_total_h = p["BOX_INTERIOR_H"] + p["MAT3"]         # 15mm (short wall full height)

    y_base = M
    y_lid  = y_base + base_w + G
    y_sw   = y_lid  + lid_w  + G

    x_right = M + base_l + G
    x_lw2   = x_right + wall_pw + G

    positions = {
        "box_base":             (M,                 y_base),
        "box_lid":              (M,                 y_lid),
        "box_long_wall_L":      (x_right,           M),
        "box_long_wall_R":      (x_lw2,             M),
        "box_short_wall_front": (M,                 y_sw),
        "box_short_wall_back":  (M + sw_bbox_w + G, y_sw),
    }

    # ── Place all parts ───────────────────────────────────────────────────
    placed = []
    for pid, local_pts, local_holes, label in parts_local:
        sx, sy = positions[pid]
        sheet_pts, sheet_holes = place(local_pts, local_holes, sx, sy)
        bb = bounding_box(sheet_pts)
        placed.append({
            "id":          pid,
            "label":       label,
            "sheet_pts":   sheet_pts,
            "sheet_holes": sheet_holes,
            "bbox":        bb,
        })

    # ── Verify: within sheet bounds ───────────────────────────────────────
    sw, sh = p["SHEET_W"], p["SHEET_H"]
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        if x0 < M - 1e-6 or y0 < M - 1e-6 or x1 > sw - M + 1e-6 or y1 > sh - M + 1e-6:
            raise ValueError(
                f"Part '{part['id']}' exceeds sheet bounds: "
                f"bbox=({x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}) "
                f"sheet=({M},{M},{sw-M},{sh-M})"
            )

    # ── Verify: no overlaps ───────────────────────────────────────────────
    for i, a in enumerate(placed):
        for j, b in enumerate(placed):
            if i >= j:
                continue
            if bboxes_overlap(a["bbox"], b["bbox"]):
                raise ValueError(
                    f"Parts '{a['id']}' and '{b['id']}' bboxes overlap: "
                    f"{a['bbox']} vs {b['bbox']}"
                )

    return placed


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------

def render(placed: list, p: dict) -> str:
    lines = [
        svg_open(p["SHEET_W"], p["SHEET_H"],
                 "BOX + STAND | 3mm BIRCH PLY 600x600mm | "
                 "RED=CUT (preview 0.3mm stroke; use --laser for 0.01mm)"),
        "",
    ]
    for part in placed:
        pid   = part["id"]
        label = part["label"]
        pts   = part["sheet_pts"]
        holes = part["sheet_holes"]
        bb    = part["bbox"]

        children = [cut_path(pts_to_path(pts), id_=f"{pid}_outer")]
        for hi, hole in enumerate(holes):
            children.append(cut_path(hole_to_path(hole), id_=f"{pid}_hole{hi}"))
        cx = (bb[0] + bb[2]) / 2.0
        cy = (bb[1] + bb[3]) / 2.0
        children.append(etch_text(cx, cy, label, size=4.0))

        lines.append(svg_group(pid, children))
        lines.append("")

    lines.append(svg_close())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def verify(placed: list, p: dict) -> list:
    results = []

    sw, sh, M = p["SHEET_W"], p["SHEET_H"], p["MARGIN"]

    # I-1: all parts within sheet bounds
    all_in = True
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        ok = x0 >= M - 1e-6 and y0 >= M - 1e-6 and x1 <= sw - M + 1e-6 and y1 <= sh - M + 1e-6
        if not ok:
            all_in = False
            results.append(("I-1", False, f"{part['id']} out of bounds: {part['bbox']}"))
    if all_in:
        results.append(("I-1", True, f"All {len(placed)} parts within sheet bounds"))

    # I-2: no overlap
    overlaps = []
    for i, a in enumerate(placed):
        for j, b in enumerate(placed):
            if i >= j:
                continue
            if bboxes_overlap(a["bbox"], b["bbox"]):
                overlaps.append(f"{a['id']} ∩ {b['id']}")
    if overlaps:
        results.append(("I-2", False, "Overlaps: " + ", ".join(overlaps)))
    else:
        results.append(("I-2", True, f"No overlaps among {len(placed)} parts"))

    # I-12: all outer paths closed
    not_closed = []
    for part in placed:
        path = pts_to_path(part["sheet_pts"])
        if not path.endswith("Z"):
            not_closed.append(part["id"])
    if not_closed:
        results.append(("I-12", False, f"Unclosed paths: {not_closed}"))
    else:
        results.append(("I-12", True, "All outer paths are closed"))

    # Spot-checks
    part_by_id = {pt["id"]: pt for pt in placed}
    checks = [
        ("box_base width",  "box_base",
         lambda bb: abs((bb[2] - bb[0]) - p["BOX_OUTER_L"]) < 0.1,
         f"expected {p['BOX_OUTER_L']:.1f}mm"),
        ("box_base height", "box_base",
         lambda bb: abs((bb[3] - bb[1]) - p["BOX_OUTER_W"]) < 0.1,
         f"expected {p['BOX_OUTER_W']:.1f}mm"),
    ]
    for name, pid, check_fn, expected in checks:
        if pid in part_by_id:
            bb = part_by_id[pid]["bbox"]
            ok = check_fn(bb)
            results.append((f"dim:{name}", ok,
                            f"OK — {expected}" if ok else f"bbox={bb} {expected}"))

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(p: dict = None) -> str:
    if p is None:
        p = DEFAULT
    placed = layout(p)
    return render(placed, p)


def write(p: dict = None, path: str = None) -> str:
    if p is None:
        p = DEFAULT
    if path is None:
        path = OUTPUT_PATH

    placed = layout(p)
    results = verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    if failures:
        msg = "\n".join(f"  {n}: {d}" for n, d in failures)
        raise ValueError(f"Box layout verification failed:\n{msg}")

    svg = render(placed, p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


def print_layout_report(p: dict = None):
    if p is None:
        p = DEFAULT
    placed = layout(p)
    results = verify(placed, p)

    print(f"\n{'='*60}")
    print(f"BOX + STAND LAYOUT REPORT  ({p['INTERIOR_W']}×{p['INTERIOR_H']}mm interior)")
    print(f"{'='*60}")
    for part in placed:
        bb = part["bbox"]
        w = bb[2] - bb[0]
        h = bb[3] - bb[1]
        print(f"  {part['id']:22s}  x={bb[0]:.1f}–{bb[2]:.1f}  y={bb[1]:.1f}–{bb[3]:.1f}"
              f"  ({w:.1f}×{h:.1f}mm)")
    print()
    all_ok = True
    for name, ok, detail in results:
        print(f"  {'✓' if ok else '✗'} {name}: {detail}")
        if not ok:
            all_ok = False
    print(f"{'='*60}")
    print(f"  {'ALL PASS' if all_ok else 'FAILURES FOUND'}")
    print(f"{'='*60}\n")
    return all_ok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate box SVG (3mm birch ply, 600×600mm)")
    ap.add_argument("--interior-w",  type=float, default=300.0, metavar="MM",
                    help="loom interior width in mm (default 300)")
    ap.add_argument("--interior-h",  type=float, default=400.0, metavar="MM",
                    help="loom interior height in mm (default 400)")
    ap.add_argument("--notch-pitch", type=float, default=10.0,  metavar="MM",
                    help="warp notch pitch in mm (default 10)")
    ap.add_argument("--output",      type=str,   default=None,  metavar="PATH",
                    help="output SVG path (default output/optional_box.svg)")
    args = ap.parse_args()
    p = make_params(
        interior_w=args.interior_w,
        interior_h=args.interior_h,
        notch_pitch=args.notch_pitch,
    )
    ok = print_layout_report(p)
    if ok:
        path = write(p, args.output)
        print(f"Written: {path}")
    else:
        print("NOT written — fix failures first.")
        sys.exit(1)
