"""
src/loom.py — Loom SVG generator.

Generates output/loom.svg: all loom parts nested on a single 600×600mm 6mm ply sheet.

Parts:
  - Top rail (with heddle holes)
  - Bottom rail
  - Stile-L, Stile-R (mirror)
  - Crossbar × 2
  - Shuttle × 2 (with lightening ellipse)
  - Beater (with grip holes)
  - Heddle bar (with heddle holes)

Every outer boundary is a single closed path.
Every inner hole is a separate closed path.
No paths overlap.

Usage:
  python3 -m src.loom              → writes output/loom.svg, prints report
  from src.loom import generate    → returns SVG string without writing
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT, make_params
from src.geometry import (
    bounding_box, bboxes_overlap, translate, mirror_x, place,
    pts_to_path, cut_path, etch_text, svg_open, svg_close, svg_group,
    rail_pts, stile_pts, crossbar_pts, shuttle_pts_with_notch, beater_pts, rect_pts,
    circle_hole, ellipse_hole, rect_hole, stadium_hole, hole_to_path,
    rail_path, beater_path, shuttle_path, rounded_pts_to_path,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "loom.svg")


# ---------------------------------------------------------------------------
# Part builders — return (local_pts, local_holes)
# All coordinates relative to the part's local bounding-box top-left.
# ---------------------------------------------------------------------------

def _notch_cxs(p: dict) -> list:
    return [p["NOTCH_START_X"] + i * p["NOTCH_PITCH"] for i in range(p["NOTCH_COUNT"])]


def build_top_rail(p: dict):
    pts = rail_pts(
        p["FRAME_OUTER_W"], p["RAIL_W"],
        p["SOCK_W"], p["TAB_L"],
        _notch_cxs(p), p["NOTCH_W"], p["NOTCH_D"],
        notches_open_down=True,
        stand_tab_l=p["STAND_RAIL_TAB_L"],
    )
    # Heddle holes: centred on rail height (y = RAIL_W/2 in local rail coords).
    # Local origin is the rail top-left bounding box corner (y=0 at outer edge).
    holes = [
        circle_hole(p["HEDDLE_HOLE_1_X"], p["RAIL_W"] / 2.0, p["HEDDLE_HOLE_R"]),
        circle_hole(p["HEDDLE_HOLE_2_X"], p["RAIL_W"] / 2.0, p["HEDDLE_HOLE_R"]),
    ]
    return pts, holes


def build_bottom_rail(p: dict):
    # Bottom rail is identical in shape to top rail (flipped during assembly).
    # Cut as the same profile; no heddle holes.
    pts = rail_pts(
        p["FRAME_OUTER_W"], p["RAIL_W"],
        p["SOCK_W"], p["TAB_L"],
        _notch_cxs(p), p["NOTCH_W"], p["NOTCH_D"],
        notches_open_down=True,
    )
    return pts, []


def build_stile_L(p: dict):
    """Stile-L: clean outline + two rect_hole mortises for crossbars (D-13)."""
    pts = stile_pts(p["STILE_W"], p["STILE_BODY_H"], p["TAB_W"], p["TAB_L"])
    # Crossbar mortise pockets on inner face (x = STILE_W - mort_d to STILE_W)
    mort_d = p["CROSS_MORT_D"]
    mort_h = p["CROSS_MORT_W"]
    mort_x = p["STILE_W"] - mort_d
    holes = [
        rect_hole(mort_x, p["CROSS1_CENTRE"] - mort_h / 2.0, mort_d, mort_h),
        rect_hole(mort_x, p["CROSS2_CENTRE"] - mort_h / 2.0, mort_d, mort_h),
    ]
    return pts, holes


def build_stile_R(p: dict):
    """Stile-R: mirror of stile_L about centre (x = STILE_W/2), holes mirrored too."""
    sl_pts, sl_holes = build_stile_L(p)
    cx = p["STILE_W"] / 2.0
    pts = mirror_x(sl_pts, cx)
    # Mirror rect_holes: x → stile_w - x - w (reflect about cx)
    holes = []
    for h in sl_holes:
        if h[0] == 'rect':
            _, hx, hy, hw, hh = h
            holes.append(rect_hole(p["STILE_W"] - hx - hw, hy, hw, hh))
    return pts, holes


def build_crossbar(p: dict):
    """Crossbar: plain rectangle INTERIOR_W × CROSS_H (D-13, no tenons)."""
    pts = crossbar_pts(p["CROSS_BODY_W"], p["CROSS_H"])
    return pts, []


def build_shuttle(p: dict):
    pts = shuttle_pts_with_notch(
        p["SHUTTLE_L"], p["SHUTTLE_W"],
        p["SHUTTLE_TAPER_L"], p["SHUTTLE_NOTCH_HW"],
    )
    # Lightening ellipse: centred on shuttle body (between the tapered zones)
    cx = p["SHUTTLE_L"] / 2.0
    cy = p["SHUTTLE_W"] / 2.0
    holes = [ellipse_hole(cx, cy, p["SHUTTLE_LIGHT_L"] / 2.0, p["SHUTTLE_LIGHT_W"] / 2.0)]
    return pts, holes


def build_beater(p: dict):
    pts = beater_pts(
        p["BEATER_W"], p["BEATER_HANDLE_H"], p["BEATER_TOOTH_H"],
        p["BEATER_TOOTH_W"], p["BEATER_TOOTH_PITCH"], p["BEATER_TOOTH_COUNT"],
        first_cx=p["BEATER_FIRST_CX"],
    )
    # 3 grip ellipses evenly spaced in handle area
    cy = p["BEATER_HANDLE_H"] / 2.0
    xs = [p["BEATER_W"] * (i + 1) / (p["BEATER_GRIP_COUNT"] + 1)
          for i in range(p["BEATER_GRIP_COUNT"])]
    holes = [ellipse_hole(x, cy, p["BEATER_GRIP_RX"], p["BEATER_GRIP_RY"]) for x in xs]
    return pts, holes


def build_heddle_bar(p: dict):
    pts = rect_pts(0.0, 0.0, p["HEDDLE_BAR_L"], p["HEDDLE_BAR_W"])
    # Holes pitch-aligned with warp notches; alternating y-offset for rigid heddle two-shed
    count = p["HEDDLE_BAR_HOLE_COUNT"]
    pitch = p["HEDDLE_BAR_HOLE_PITCH"]
    span = (count - 1) * pitch
    x0 = (p["HEDDLE_BAR_L"] - span) / 2.0   # x of first hole in local coords
    cy = p["HEDDLE_BAR_W"] / 2.0
    # D-32: alternating holes (controlled threads) and slots (free threads)
    # Even positions: stadium_hole centred on bar — thread moves with heddle bar
    # Odd positions: rect_hole (slot) centred on bar — thread slides freely
    slot_w = p["HEDDLE_BAR_SLOT_W"]
    slot_h = p["HEDDLE_BAR_SLOT_H"]
    holes = []
    for i in range(count):
        x = x0 + i * pitch
        if i % 2 == 0:
            holes.append(stadium_hole(x, cy, p["HEDDLE_BAR_HOLE_R"], p["HEDDLE_BAR_HOLE_H"]))
        else:
            # D-34: stadium (rounded ends) instead of rect — same r as H holes, no sharp corners
            holes.append(stadium_hole(x, cy, p["HEDDLE_BAR_HOLE_R"], slot_h))
    return pts, holes


# ---------------------------------------------------------------------------
# Layout — place all parts on the sheet, verify, return placed part records
# ---------------------------------------------------------------------------

def layout(p: dict) -> list:
    """
    Place all loom parts on the sheet.

    Returns a list of dicts:
      { 'id', 'label', 'sheet_pts', 'sheet_holes', 'bbox' }

    Raises ValueError if any part exceeds sheet bounds or parts overlap.
    """
    M = p["MARGIN"]   # 2mm minimum clearance to sheet edges
    G = 2.0           # mm inter-part gap

    # ── Build all parts in local coords ──────────────────────────────────
    parts_local = [
        ("crossbar_1",   *build_crossbar(p),    "CROSSBAR 1"),
        ("crossbar_2",   *build_crossbar(p),    "CROSSBAR 2"),
        ("top_rail",     *build_top_rail(p),    "TOP RAIL"),
        ("bottom_rail",  *build_bottom_rail(p), "BOTTOM RAIL"),
        ("stile_L",      *build_stile_L(p),     "STILE L"),
        ("stile_R",      *build_stile_R(p),     "STILE R"),
        ("heddle_bar",   *build_heddle_bar(p),  "HEDDLE BAR"),
        ("shuttle_1",    *build_shuttle(p),      "SHUTTLE 1"),
        ("shuttle_2",    *build_shuttle(p),      "SHUTTLE 2"),
        ("beater",       *build_beater(p),       "BEATER"),
    ]

    # ── Sheet positions (bounding-box top-left) ────────────────────────
    # Left column: crossbars, rails, stiles (stack vertically)
    cb_h  = p["CROSS_H"]
    rl_h  = p["RAIL_W"] + p["NOTCH_D"]   # rail bbox height (incl. notches)
    st_h  = p["STILE_BODY_H"] + 2 * p["TAB_L"]  # stile bbox height

    y = M
    cb1_pos  = (M, y);  y += cb_h + G
    cb2_pos  = (M, y);  y += cb_h + G
    tr_pos   = (M, y);  y += rl_h + G
    br_pos   = (M, y);  y += rl_h + G
    stile_y  = y                          # stiles start here

    sl_pos = (M, stile_y)
    sr_pos = (M + p["STILE_W"] + G, stile_y)

    # Right area: accessories beside stiles
    x_right = M + p["STILE_W"] + G + p["STILE_W"] + G  # = 2+22+2+22+2 = 50mm
    y_r = stile_y

    hb_pos  = (x_right, y_r);  y_r += p["HEDDLE_BAR_W"] + G
    sh1_pos = (x_right, y_r);  y_r += p["SHUTTLE_W"] + G
    sh2_pos = (x_right, y_r);  y_r += p["SHUTTLE_W"] + G
    bt_pos  = (x_right, y_r)

    positions = {
        "crossbar_1":  cb1_pos,
        "crossbar_2":  cb2_pos,
        "top_rail":    tr_pos,
        "bottom_rail": br_pos,
        "stile_L":     sl_pos,
        "stile_R":     sr_pos,
        "heddle_bar":  hb_pos,
        "shuttle_1":   sh1_pos,
        "shuttle_2":   sh2_pos,
        "beater":      bt_pos,
    }

    # ── Rounded-path overrides (D-25): rail notches + beater teeth ────
    ncxs = _notch_cxs(p)
    cr = p["CORNER_R"]

    def _rail_outer_path(sx, sy, open_down=True):
        return rail_path(
            p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
            ncxs, p["NOTCH_W"], p["NOTCH_D"],
            corner_r=cr, notches_open_down=open_down, ox=sx, oy=sy,
        )

    def _beater_outer_path(sx, sy):
        return beater_path(
            p["BEATER_W"], p["BEATER_HANDLE_H"], p["BEATER_TOOTH_H"],
            p["BEATER_TOOTH_W"], p["BEATER_TOOTH_PITCH"], p["BEATER_TOOTH_COUNT"],
            corner_r=cr, ox=sx, oy=sy, first_cx=p["BEATER_FIRST_CX"],
        )

    def _shuttle_outer_path(sx, sy):
        return shuttle_path(
            p["SHUTTLE_L"], p["SHUTTLE_W"], p["SHUTTLE_TAPER_L"], p["SHUTTLE_NOTCH_HW"],
            corner_r=cr, ox=sx, oy=sy,
        )

    hb_cr = p["HEDDLE_BAR_CORNER_R"]

    _outer_path_fns = {
        "top_rail":    lambda sx, sy: _rail_outer_path(sx, sy, open_down=True),
        "bottom_rail": lambda sx, sy: _rail_outer_path(sx, sy, open_down=True),
        "beater":      lambda sx, sy: _beater_outer_path(sx, sy),
        "shuttle_1":   lambda sx, sy: _shuttle_outer_path(sx, sy),
        "shuttle_2":   lambda sx, sy: _shuttle_outer_path(sx, sy),
        "heddle_bar":  lambda sx, sy: rounded_pts_to_path(
            rect_pts(0.0, 0.0, p["HEDDLE_BAR_L"], p["HEDDLE_BAR_W"]),
            corner_r=hb_cr, ox=sx, oy=sy,
        ),
    }

    # ── Place parts ───────────────────────────────────────────────────
    placed = []
    for pid, local_pts, local_holes, label in parts_local:
        sx, sy = positions[pid]
        sheet_pts, sheet_holes = place(local_pts, local_holes, sx, sy)
        bb = bounding_box(sheet_pts)
        entry = {
            "id":          pid,
            "label":       label,
            "sheet_pts":   sheet_pts,
            "sheet_holes": sheet_holes,
            "bbox":        bb,
        }
        if pid in _outer_path_fns:
            entry["outer_path"] = _outer_path_fns[pid](sx, sy)
        # D-27: custom label positions — avoid placing labels on cut-outs
        bb = entry["bbox"]
        bcx = (bb[0] + bb[2]) / 2.0
        if pid in ("shuttle_1", "shuttle_2"):
            # Place above lightening ellipse (top solid strip y=0..8mm local)
            ellipse_top = bb[1] + p["SHUTTLE_W"] / 2.0 - p["SHUTTLE_LIGHT_W"] / 2.0
            entry["label_xy"] = (bcx, ellipse_top - 2.0)
        elif pid == "heddle_bar":
            # D-32: holes/slots all centred on bar. Top solid strip: y=0..3.5mm local.
            # Place label at HEDDLE_BAR_W/4 from bar top (midpoint of solid strip above holes).
            entry["label_xy"] = (bcx, bb[1] + p["HEDDLE_BAR_W"] / 4.0)
            # D-33: per-position H/S etch labels in the strip below holes/slots.
            # Stadium holes (even): bottom at bar_cy + HOLE_H/2. 7mm strip below → H+S both fit.
            # Rect slots (odd): bottom at bar_cy + SLOT_H/2. 4mm strip below → S only.
            sx_hb, sy_hb = positions["heddle_bar"]
            count_hb = p["HEDDLE_BAR_HOLE_COUNT"]
            pitch_hb = p["HEDDLE_BAR_HOLE_PITCH"]
            span_hb  = (count_hb - 1) * pitch_hb
            x0_hb    = (p["HEDDLE_BAR_L"] - span_hb) / 2.0 + sx_hb  # sheet x of first hole
            bar_cy   = sy_hb + p["HEDDLE_BAR_W"] / 2.0
            bar_bot  = sy_hb + p["HEDDLE_BAR_W"]
            hole_labels = []
            for i in range(count_hb):
                hx = x0_hb + i * pitch_hb
                if i % 2 == 0:
                    # Stadium hole bottom: bar_cy + HOLE_H/2
                    hole_bot = bar_cy + p["HEDDLE_BAR_HOLE_H"] / 2.0
                    hole_labels.append((hx, hole_bot + 2.5, "H", 2.0))
                    if bar_bot - (hole_bot + 5.5) >= 1.0:
                        hole_labels.append((hx, hole_bot + 5.5, "S", 2.0))
                else:
                    # Rect slot bottom: bar_cy + SLOT_H/2
                    slot_bot = bar_cy + p["HEDDLE_BAR_SLOT_H"] / 2.0
                    if bar_bot - (slot_bot + 1.5) >= 1.0:
                        hole_labels.append((hx, slot_bot + 1.5, "S", 2.0))
            entry["hole_labels"] = hole_labels
        placed.append(entry)

    # ── Verify: all parts within sheet bounds ─────────────────────────
    sw, sh = p["SHEET_W"], p["SHEET_H"]
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        if x0 < M - 1e-6 or y0 < M - 1e-6 or x1 > sw - M + 1e-6 or y1 > sh - M + 1e-6:
            raise ValueError(
                f"Part '{part['id']}' exceeds sheet bounds: "
                f"bbox=({x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}) "
                f"sheet=({M},{M},{sw-M},{sh-M})"
            )

    # ── Verify: no part bounding boxes overlap ────────────────────────
    for i, a in enumerate(placed):
        for j, b in enumerate(placed):
            if i >= j:
                continue
            if bboxes_overlap(a["bbox"], b["bbox"]):
                raise ValueError(
                    f"Parts '{a['id']}' and '{b['id']}' bounding boxes overlap: "
                    f"{a['bbox']} vs {b['bbox']}"
                )

    return placed


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------

def render(placed: list, p: dict) -> str:
    """Convert a placed-parts list to an SVG string."""
    lines = [
        svg_open(p["SHEET_W"], p["SHEET_H"],
                 "FRAME LOOM v6 | 6mm BIRCH PLY 600x600mm | "
                 "RED=CUT preview 0.1mm — change to 0.01mm for laser"),
        "",
    ]

    for part in placed:
        pid    = part["id"]
        label  = part["label"]
        pts    = part["sheet_pts"]
        holes  = part["sheet_holes"]
        bb     = part["bbox"]

        children = []
        # Outer boundary (use rounded path override if available, D-25)
        outline = part.get("outer_path") or pts_to_path(pts)
        children.append(cut_path(outline, id_=f"{pid}_outer"))
        # Inner holes
        for hi, hole in enumerate(holes):
            children.append(cut_path(hole_to_path(hole), id_=f"{pid}_hole{hi}"))
        # Label (etch): use custom position if set (D-27), else bbox centre
        cx = (bb[0] + bb[2]) / 2.0
        cy = (bb[1] + bb[3]) / 2.0
        lx, ly = part.get("label_xy", (cx, cy))
        children.append(etch_text(lx, ly, label, size=4.0))
        # Per-hole H/S labels (D-33): heddle bar only
        for (elx, ely, letter, esz) in part.get("hole_labels", []):
            children.append(etch_text(elx, ely, letter, size=esz))

        lines.append(svg_group(pid, children))
        lines.append("")

    lines.append(svg_close())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verify — check the placed layout against invariants
# ---------------------------------------------------------------------------

def verify(placed: list, p: dict) -> list:
    """
    Run post-layout checks. Returns list of (check_name, ok, detail) tuples.
    These are checks that require the full placed layout (I-1, I-2, I-12 partial).
    """
    results = []

    # I-1: all parts within sheet bounds
    sw, sh, M = p["SHEET_W"], p["SHEET_H"], p["MARGIN"]
    all_in = True
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        ok = x0 >= M - 1e-6 and y0 >= M - 1e-6 and x1 <= sw - M + 1e-6 and y1 <= sh - M + 1e-6
        if not ok:
            all_in = False
            results.append(("I-1", False, f"{part['id']} out of bounds: {part['bbox']}"))
    if all_in:
        results.append(("I-1", True, f"All {len(placed)} parts within sheet bounds"))

    # I-2: no part overlap
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

    # I-12: outer paths are closed (end with Z)
    not_closed = []
    for part in placed:
        path = pts_to_path(part["sheet_pts"])
        if not path.endswith("Z"):
            not_closed.append(part["id"])
    if not_closed:
        results.append(("I-12", False, f"Unclosed paths: {not_closed}"))
    else:
        results.append(("I-12", True, "All outer paths are closed"))

    # Spot-check dimensions
    checks = [
        ("stile_L height", "stile_L",
         lambda bb: abs((bb[3] - bb[1]) - p["STILE_TOTAL_H"]) < 0.1,
         f"expected {p['STILE_TOTAL_H']:.1f}mm"),
        ("stile_L width", "stile_L",
         lambda bb: abs((bb[2] - bb[0]) - p["STILE_W"]) < 0.1,
         f"expected {p['STILE_W']:.1f}mm"),
        ("top_rail width", "top_rail",
         lambda bb: abs((bb[2] - bb[0]) - (p["FRAME_OUTER_W"] + 2.0 * p["STAND_RAIL_TAB_L"])) < 0.1,
         f"expected {p['FRAME_OUTER_W'] + 2.0 * p['STAND_RAIL_TAB_L']:.1f}mm"),
        ("crossbar_1 length", "crossbar_1",
         lambda bb: abs((bb[2] - bb[0]) - p["CROSS_TOTAL_L"]) < 0.1,
         f"expected {p['CROSS_TOTAL_L']:.1f}mm"),
    ]
    part_by_id = {pt["id"]: pt for pt in placed}
    for name, pid, check_fn, expected in checks:
        if pid in part_by_id:
            bb = part_by_id[pid]["bbox"]
            ok = check_fn(bb)
            results.append((f"dim:{name}", ok,
                            f"bbox={bb} {expected}" if not ok else f"OK — {expected}"))

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(p: dict = None) -> str:
    """Generate loom SVG string. Does not write to disk."""
    if p is None:
        p = DEFAULT
    placed = layout(p)
    return render(placed, p)


def write(p: dict = None, path: str = None) -> str:
    """Generate loom SVG, verify, write to disk. Returns file path."""
    if p is None:
        p = DEFAULT
    if path is None:
        path = OUTPUT_PATH

    placed = layout(p)

    # Run verify before writing
    results = verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    if failures:
        msg = "\n".join(f"  {n}: {d}" for n, d in failures)
        raise ValueError(f"Layout verification failed before writing SVG:\n{msg}")

    svg = render(placed, p)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)

    return path


def print_layout_report(p: dict = None):
    """Print a layout report for the given params."""
    if p is None:
        p = DEFAULT
    placed = layout(p)
    results = verify(placed, p)

    print(f"\n{'='*60}")
    print(f"LOOM LAYOUT REPORT  ({p['INTERIOR_W']}×{p['INTERIOR_H']}mm interior)")
    print(f"{'='*60}")
    for part in placed:
        bb = part["bbox"]
        w = bb[2] - bb[0]
        h = bb[3] - bb[1]
        print(f"  {part['id']:15s}  x={bb[0]:.1f}–{bb[2]:.1f}  y={bb[1]:.1f}–{bb[3]:.1f}"
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate loom SVG (6mm birch ply, 600×600mm)")
    ap.add_argument("--interior-w",          type=float, default=300.0, metavar="MM",
                    help="weaving interior width in mm (default 300)")
    ap.add_argument("--interior-h",          type=float, default=400.0, metavar="MM",
                    help="weaving interior height in mm (default 400)")
    ap.add_argument("--notch-pitch",         type=float, default=10.0,  metavar="MM",
                    help="warp notch pitch in mm (default 10)")
    ap.add_argument("--beater-tooth-divisor",type=int,   default=1,     metavar="N",
                    help="1=tooth per gap (default), 2=every other gap, etc.")
    ap.add_argument("--output",              type=str,   default=None,  metavar="PATH",
                    help="output SVG path (default output/loom.svg)")
    args = ap.parse_args()
    p = make_params(
        interior_w=args.interior_w,
        interior_h=args.interior_h,
        notch_pitch=args.notch_pitch,
        beater_tooth_divisor=args.beater_tooth_divisor,
    )
    ok = print_layout_report(p)
    if ok:
        path = write(p, args.output)
        print(f"Written: {path}")
    else:
        print("NOT written — fix failures first.")
        sys.exit(1)
