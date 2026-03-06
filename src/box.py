"""
src/box.py — Box + A-frame stand SVG generator.

Generates output/box.svg: all box panels and stand pieces on a single
600×600mm 3mm ply sheet.

Parts:
  Box (6 panels, glue assembly):
    - box_base:          BOX_OUTER_L × BOX_OUTER_W (floor panel)
    - box_lid:           BOX_INTERIOR_L × BOX_INTERIOR_W (rests on top)
    - box_long_wall_L/R: BOX_OUTER_L × BOX_INTERIOR_H (×2)
    - box_short_wall_front/back: BOX_INTERIOR_W × BOX_INTERIOR_H (×2)

  A-frame stand (3 pieces, press-fit assembly):
    - stand_L:           leg with U-notch at top + spreader mortise hole
    - stand_R:           mirror_x of stand_L
    - stand_spreader:    flat bar with tenons each end

Assembly note:
  Box walls butt-joint to base (glue). Lid rests on top.
  Stand legs press-fit onto spreader tenons; loom stile rests in U-notch.

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
    rect_pts, stand_leg_pts,
    rect_hole, hole_to_path,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "box.svg")


# ---------------------------------------------------------------------------
# Part builders — return (local_pts, local_holes)
# ---------------------------------------------------------------------------

def build_box_base(p: dict):
    """Floor panel: BOX_OUTER_L × BOX_OUTER_W."""
    pts = rect_pts(0.0, 0.0, p["BOX_OUTER_L"], p["BOX_OUTER_W"])
    return pts, []


def build_box_lid(p: dict):
    """Lid panel: BOX_INTERIOR_L × BOX_INTERIOR_W (rests on top of box walls)."""
    pts = rect_pts(0.0, 0.0, p["BOX_INTERIOR_L"], p["BOX_INTERIOR_W"])
    return pts, []


def build_box_long_wall(p: dict):
    """
    Long wall panel: placed in 'portrait' orientation on sheet.
    Local coords: BOX_INTERIOR_H wide × BOX_OUTER_L tall.
    (Rotate mentally when assembling: the 'tall' axis becomes the box length.)
    """
    pts = rect_pts(0.0, 0.0, p["BOX_INTERIOR_H"], p["BOX_OUTER_L"])
    return pts, []


def build_box_short_wall(p: dict):
    """
    Short wall panel: BOX_INTERIOR_W wide × BOX_INTERIOR_H tall.
    Sits between the long walls at each end of the box.
    """
    pts = rect_pts(0.0, 0.0, p["BOX_INTERIOR_W"], p["BOX_INTERIOR_H"])
    return pts, []


def build_stand_leg(p: dict):
    """
    Stand leg: 40×300mm rectangle with U-notch at top (for loom stile)
    and a rectangular mortise hole near the bottom (for spreader tenon).

    Local origin: top-left bounding box corner.
    Notch open at y=0 (top of piece).
    Mortise hole: STAND_SPREAD_MORT_D × STAND_SPREAD_MORT_W, centred on x,
    at 30mm from bottom.
    """
    pts = stand_leg_pts(
        p["STAND_LEG_W"], p["STAND_LEG_L"],
        p["STAND_NOTCH_W"], p["STAND_NOTCH_D"],
    )
    # Rectangular mortise for spreader tenon — centred on leg width
    mort_d = p["STAND_SPREAD_MORT_D"]   # 15mm (tenon length, along x)
    mort_w = p["STAND_SPREAD_MORT_W"]   # 3.1mm (tenon thickness, along y)
    mort_x = (p["STAND_LEG_W"] - mort_d) / 2.0          # = 12.5mm
    mort_y = p["STAND_LEG_L"] - 30.0 - mort_w / 2.0     # 30mm from bottom
    holes = [rect_hole(mort_x, mort_y, mort_d, mort_w)]
    return pts, holes


def build_stand_spreader(p: dict):
    """
    Stand spreader: flat bar spanning frame outer width, with tenons each end.
    Full-height tenons (ten_w == spread_w) → simple rectangle.
    Total length: STAND_SPREAD_L + 2×STAND_SPREAD_TEN_L.
    """
    total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]
    pts = rect_pts(0.0, 0.0, total_l, p["STAND_SPREAD_W"])
    return pts, []


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout(p: dict) -> list:
    """
    Place all 9 parts on the 600×600mm 3mm ply sheet.

    Returns list of dicts: { 'id', 'label', 'sheet_pts', 'sheet_holes', 'bbox' }
    Raises ValueError if any part exceeds sheet bounds or parts overlap.

    Sheet layout (all measurements in mm, origin top-left):
      Column A (x=2..): base, lid, long walls stacked; bottom strip for spreader+short walls
      Column B (x=470..): long walls in portrait; stand legs beside them
    """
    M  = p["MARGIN"]   # = 2mm
    G  = 2.0           # inter-part gap

    # ── Part local builds ───────────────────────────────────────────────────
    leg_pts, leg_holes = build_stand_leg(p)
    leg_pts_r = mirror_x(leg_pts, p["STAND_LEG_W"] / 2.0)

    parts_local = [
        ("box_base",          *build_box_base(p),      "BOX BASE"),
        ("box_lid",           *build_box_lid(p),       "BOX LID"),
        ("box_long_wall_L",   *build_box_long_wall(p), "LONG WALL L"),
        ("box_long_wall_R",   *build_box_long_wall(p), "LONG WALL R"),
        ("box_short_wall_front", *build_box_short_wall(p), "SHORT WALL FR"),
        ("box_short_wall_back",  *build_box_short_wall(p), "SHORT WALL BK"),
        ("stand_L",           leg_pts,   leg_holes,    "STAND L"),
        ("stand_R",           leg_pts_r, leg_holes,    "STAND R"),
        ("stand_spreader",    *build_stand_spreader(p), "STAND SPREADER"),
    ]

    # ── Sheet positions (bounding-box top-left) ──────────────────────────
    base_l  = p["BOX_OUTER_L"]                    # 466mm
    base_w  = p["BOX_OUTER_W"]                    # 236mm
    lid_l   = p["BOX_INTERIOR_L"]                 # 460mm
    lid_w   = p["BOX_INTERIOR_W"]                 # 230mm
    wall_h  = p["BOX_INTERIOR_H"]                 # 8mm (long wall portrait height)
    wall_l  = p["BOX_OUTER_L"]                    # 466mm (long wall portrait length = tall dim)
    sw_l    = p["BOX_INTERIOR_W"]                 # 230mm (short wall long dim)
    leg_w   = p["STAND_LEG_W"]                    # 40mm
    leg_l   = p["STAND_LEG_L"]                    # 300mm
    spr_l   = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]  # 374mm
    spr_w   = p["STAND_SPREAD_W"]                 # 40mm

    # Left column: base, lid (stacked vertically)
    y_base = M
    y_lid  = y_base + base_w + G      # 240mm

    # Right column (x ≥ 470): long walls in portrait + stand legs
    x_right = M + base_l + G          # = 2+466+2 = 470mm
    y_lwall = M                        # start at top

    # Long wall portrait dims: wall_h wide, wall_l tall in local coords
    x_lw1   = x_right
    x_lw2   = x_lw1 + wall_h + G      # = 470+8+2 = 480mm

    x_leg1  = x_lw2 + wall_h + G      # = 480+8+2 = 490mm
    x_leg2  = x_leg1 + leg_w + G      # = 490+40+2 = 532mm

    # Bottom strip (below lid, y ≥ y_lid + lid_w + G)
    y_bottom = y_lid + lid_w + G       # = 240+230+2 = 472mm

    y_spr   = y_bottom
    y_sw    = y_spr + spr_w + G        # = 472+40+2 = 514mm

    x_sw1   = M
    x_sw2   = x_sw1 + sw_l + G        # = 2+230+2 = 234mm

    positions = {
        "box_base":          (M,      y_base),
        "box_lid":           (M,      y_lid),
        "box_long_wall_L":   (x_lw1,  y_lwall),
        "box_long_wall_R":   (x_lw2,  y_lwall),
        "stand_L":           (x_leg1, y_lwall),
        "stand_R":           (x_leg2, y_lwall),
        "stand_spreader":    (M,      y_spr),
        "box_short_wall_front": (x_sw1, y_sw),
        "box_short_wall_back":  (x_sw2, y_sw),
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
                 "RED=CUT preview 0.1mm — change to 0.01mm for laser"),
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
        ("stand_L height",  "stand_L",
         lambda bb: abs((bb[3] - bb[1]) - p["STAND_LEG_L"]) < 0.1,
         f"expected {p['STAND_LEG_L']:.1f}mm"),
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
    ok = print_layout_report()
    if ok:
        path = write()
        print(f"Written: {path}")
    else:
        print("NOT written — fix failures first.")
        sys.exit(1)
