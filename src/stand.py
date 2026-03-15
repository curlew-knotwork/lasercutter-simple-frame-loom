"""
src/stand.py — 2-piece triangular X easel SVG generator (D-23).

D-23: 2-piece triangular X easel — cross-halving half-lap joint at centre.
Two 6mm ply right-triangle pieces with DIFFERENT slot geometry that mates:
  Piece A: slot from horizontal top edge (y=0), depth W/4 = 20mm.
  Piece B: slot from hypotenuse edge (y≈W/2 at crossing), depth W/4 = 20mm.
Both slot bottoms meet at y=W/4 from the top edge; the pieces interlock there.

Piece geometry (local coords, x=length axis, y=width axis):
  Right triangle: (0,0), (L,0), (0,W).
    - Top edge horizontal at y=0: from (0,0) to (L,0).
    - Hypotenuse: from (L,0) to (0,W).
    - Foot edge vertical at x=0: from (0,W) to (0,0).
  At x=L/2, triangle height = W/2; each slot occupies half of that = W/4 deep.
  Foot ledge: protrudes from foot end in +y direction (outward when standing on short leg).
    Rises TAB_H above ground at x=0, extends TAB_L deep, creating ledge for loom bottom rail.
  Bump: mechanical stop at outer ledge end. BUMP_H tall × BUMP_L deep.
  Total polygon: 12 points (CW winding).

Assembly:
  stand_x_a — slot from top edge; ledge protrudes in +y from foot corner.
  stand_x_b — slot from hypotenuse edge; same ledge orientation.
  Stand upright on short legs (x=0 edge horizontal). Ledge at foot corner holds loom bottom rail.
  Slide piece B's slot down over piece A from above; slots interlock at x=L/2.

Flat-pack: both pieces (450×110mm bounding box each) lay side-by-side in box layer 2.

Usage:
  python3 -m src.stand           → writes output/optional_loom_stand.svg
  from src.stand import generate → returns SVG string
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT, make_params
from src.geometry import (
    bounding_box, bboxes_overlap, place,
    pts_to_path, cut_path, etch_text, svg_open, svg_close, svg_group,
)

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "optional_loom_stand.svg"
)


# ---------------------------------------------------------------------------
# Part builder
# ---------------------------------------------------------------------------

def build_stand_x_piece(p: dict):
    """
    Build one X-piece polygon (D-23) — right triangle with slot and foot tab+bump.

    Polygon trace (CW from top-left of foot):
      (0, 0)                                         ← foot top
      (slot_cx − slot_w/2, 0)                        ← top edge before slot
      (slot_cx − slot_w/2, slot_d)                   ← slot left wall
      (slot_cx + slot_w/2, slot_d)                   ← slot bottom
      (slot_cx + slot_w/2, 0)                        ← slot right wall top
      (L, 0)                                         ← triangle tip (hyp starts here)
      (0, W)                                         ← hypotenuse meets foot (straight edge L→0,W)
      (−TAB_L − BUMP_L, W)                           ← tab+bump outer bottom
      (−TAB_L − BUMP_L, W − TAB_H − BUMP_H)         ← outer bump top
      (−TAB_L, W − TAB_H − BUMP_H)                  ← bump step inner top
      (−TAB_L, W − TAB_H)                            ← tab outer top
      (0, W − TAB_H)                                 ← tab inner top (at foot edge)
      → closes to (0, 0) via foot edge

    Returns (pts, holes) — holes is always [].
    """
    L      = p["STAND_X_L"]
    W      = p["STAND_X_W"]
    slot_w = p["STAND_X_SLOT_W"]
    slot_d = p["STAND_X_SLOT_D"]
    tab_l  = p["STAND_X_TAB_L"]
    tab_h  = p["STAND_X_TAB_H"]
    bump_l = p["STAND_X_BUMP_L"]
    bump_h = p["STAND_X_BUMP_H"]

    slot_cx = L / 2.0

    # Hyp intercept: point on hyp at x=tab_h from foot (y = W*(1−tab_h/L))
    hyp_y_tab = W * (1.0 - tab_h / L)

    pts = [
        (0.0,                    0.0),                    #  1 foot top
        (slot_cx - slot_w / 2.0, 0.0),                    #  2 top edge before slot
        (slot_cx - slot_w / 2.0, slot_d),                 #  3 slot left wall
        (slot_cx + slot_w / 2.0, slot_d),                 #  4 slot bottom
        (slot_cx + slot_w / 2.0, 0.0),                    #  5 slot right wall top
        (L,                      0.0),                    #  6 triangle tip
        (tab_h,                  hyp_y_tab),              #  7 hyp walk to tab: connected along hyp edge
        (tab_h,                  hyp_y_tab + tab_l),      #  8 ledge outer (tab extends +y from hyp)
        (tab_h + bump_h,         hyp_y_tab + tab_l),      #  9 bump inner face
        (tab_h + bump_h,         hyp_y_tab + tab_l + bump_l),  # 10 bump outer
        (0.0,                    W + tab_l + bump_l),     # 11 return to foot edge
    ]
    return pts, []


def build_stand_x_piece_b(p: dict):
    """
    Build piece B — same right triangle + tab/bump, but slot from HYPOTENUSE side.

    For the cross-halving X joint to mate:
      Piece A slot: from top edge (y=0) DOWN to y=slot_d=W/4.   Material: y=slot_d..hyp_y.
      Piece B slot: from hyp edge (y≈W/2) UP   to y=slot_d=W/4. Material: y=0..slot_d.
    At x=L/2: hyp_y=W/2=40mm, slot_d=W/4=20mm — both slot bottoms meet at y=20mm. ✓

    Polygon trace (CW, 12 points):
      (0, 0)                            ← foot top
      (L, 0)                            ← tip (top edge continuous, no slot here)
      (slot_cx+slot_w/2, hyp_y_right)   ← hyp before slot (right wall top)
      (slot_cx+slot_w/2, slot_d)        ← slot right wall bottom
      (slot_cx-slot_w/2, slot_d)        ← slot bottom
      (slot_cx-slot_w/2, hyp_y_left)    ← hyp after slot (left wall top)
      (0, W)                            ← hyp meets foot
      (−TAB_L−BUMP_L, W)               ← tab+bump outer bottom
      (−TAB_L−BUMP_L, W−TAB_H−BUMP_H) ← outer bump top
      (−TAB_L, W−TAB_H−BUMP_H)        ← bump step inner top
      (−TAB_L, W−TAB_H)               ← tab outer top
      (0, W−TAB_H)                     ← tab inner top
      → closes to (0, 0) via foot edge

    Returns (pts, holes) — holes is always [].
    """
    L      = p["STAND_X_L"]
    W      = p["STAND_X_W"]
    slot_w = p["STAND_X_SLOT_W"]
    slot_d = p["STAND_X_SLOT_D"]
    tab_l  = p["STAND_X_TAB_L"]
    tab_h  = p["STAND_X_TAB_H"]
    bump_l = p["STAND_X_BUMP_L"]
    bump_h = p["STAND_X_BUMP_H"]

    slot_cx = L / 2.0
    # Hyp: y = W*(1 - x/L). At slot walls:
    hyp_y_right = W * (1.0 - (slot_cx + slot_w / 2.0) / L)  # smaller y (right wall, x larger)
    hyp_y_left  = W * (1.0 - (slot_cx - slot_w / 2.0) / L)  # larger y  (left wall,  x smaller)
    # slot_d = W/4 = slot bottom y from top — same as piece A's slot bottom. Slots mate there.

    # Hyp intercept: point on hyp at x=tab_h from foot (y = W*(1−tab_h/L))
    hyp_y_tab = W * (1.0 - tab_h / L)

    pts = [
        (0.0,                    0.0),                    #  1 foot top
        (L,                      0.0),                    #  2 tip (no slot on long leg)
        (slot_cx + slot_w / 2.0, hyp_y_right),           #  3 hyp to right slot wall
        (slot_cx + slot_w / 2.0, slot_d),                 #  4 slot right wall bottom
        (slot_cx - slot_w / 2.0, slot_d),                 #  5 slot bottom
        (slot_cx - slot_w / 2.0, hyp_y_left),            #  6 back to hyp (left wall top)
        (tab_h,                  hyp_y_tab),              #  7 hyp walk to tab: connected along hyp edge
        (tab_h,                  hyp_y_tab + tab_l),      #  8 ledge outer (tab extends +y from hyp)
        (tab_h + bump_h,         hyp_y_tab + tab_l),      #  9 bump inner face
        (tab_h + bump_h,         hyp_y_tab + tab_l + bump_l),  # 10 bump outer
        (0.0,                    W + tab_l + bump_l),     # 11 return to foot edge
    ]
    return pts, []


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout(p: dict) -> list:
    """
    Place both X pieces on the 600×600mm 6mm ply sheet.

    Layout (M = MARGIN = 2mm, G = 2mm gap, TAB_OFF = TAB_L + BUMP_L = 30mm):
      stand_x_a at (M + TAB_OFF, M)           — shifted right so tab fits at left margin
      stand_x_b at (M + TAB_OFF, M + W + G)   — below piece a

    The tab protrudes in −x from each piece, reaching x = M at the sheet boundary.

    Returns list of dicts: {id, label, sheet_pts, sheet_holes, bbox}.
    Raises ValueError if any part exceeds sheet bounds or parts overlap.
    """
    M = p["MARGIN"]
    G = 2.0

    pts_a, holes_a = build_stand_x_piece(p)
    pts_b, holes_b = build_stand_x_piece_b(p)

    W     = p["STAND_X_W"]
    TAB_L = p["STAND_X_TAB_L"]
    BUMP_L = p["STAND_X_BUMP_L"]
    H = W + TAB_L + BUMP_L  # total piece height: triangle + ledge + bump

    # place() maps sx to the left edge of the local bounding box (x=0, foot edge).
    # Tab protrudes in +y (outward from foot when standing on short leg), no -x protrusion.
    parts_local = [
        ("stand_x_a", pts_a, holes_a, "STAND X-A", M,         M),
        ("stand_x_b", pts_b, holes_b, "STAND X-B", M, M + H + G),
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
        holes = [cut_path(pts_to_path(h)) for h in part["sheet_holes"]]
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
        print(f"  {part['id']:12s}  x={bb[0]:.1f}–{bb[2]:.1f}  y={bb[1]:.1f}–{bb[3]:.1f}"
              f"  ({bb[2]-bb[0]:.1f}×{bb[3]-bb[1]:.1f}mm)")
