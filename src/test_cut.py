"""
src/test_cut.py — Calibration / fit-test SVG for 3mm ply scrap.

Cut these pieces BEFORE the full box sheet to verify joint clearances.
Five pieces exercise every joint type in the box:

  tc_socket      — long-wall end slice: corner socket + base tab
  tc_tab         — short-wall end slice: corner tab + lid slot + base tab
  tc_base_notch  — base edge strip: edge notch for base tab fit-test
  tc_lid         — lid strip: slides through tc_tab lid slot
  tc_lid_slot    — short-wall top: lid slot in isolation

Assembly test:
  1. tc_tab corner tab → tc_socket corner socket  (wall-to-wall fit)
  2. tc_socket base tab → tc_base_notch edge notch (wall-to-base fit)
  3. tc_lid strip → tc_lid_slot top slot          (lid slide fit)

Sheet: 3mm scrap, TC_SHEET_W × TC_SHEET_H mm.

Usage:
  python3 -m src.test_cut       → writes output/test_cut.svg
  from src.test_cut import generate
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT, make_params
from src.geometry import (
    bounding_box, bboxes_overlap, place,
    pts_to_path, cut_path, etch_text,
    svg_open, svg_close, svg_group,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "test_cut.svg")

# Small scrap sheet
TC_SHEET_W = 200.0
TC_SHEET_H = 100.0

PIECE_IDS = [
    "tc_socket",
    "tc_tab",
    "tc_base_notch",
    "tc_lid",
    "tc_lid_slot",
]

# Sample piece length (along joint direction) — 30mm gives easy handling
TC_SAMPLE_L = 30.0


# ---------------------------------------------------------------------------
# Piece builders — return (local_pts, local_holes, label)
# ---------------------------------------------------------------------------

def _build_tc_socket(p: dict):
    """
    Long-wall end slice: shows corner socket at top + base tab on right edge.
    Width (x): BOX_INTERIOR_H (wall height, no base tab on this cross-section).
    Height (y): TC_SAMPLE_L.
    Corner socket at y=0: MAT3 deep × BOX_TAB_W wide, centred on BOX_INTERIOR_H.
    Base tab at x=h, centered on y, width=BOX_TAB_W, depth=MAT3.
    """
    h    = p["BOX_INTERIOR_H"]   # 12mm  (wall height only, not incl. base tab)
    l    = TC_SAMPLE_L           # 30mm
    t    = p["MAT3"]             # 3mm
    tw   = p["BOX_TAB_W"]        # 4mm
    tw2  = tw / 2.0
    sx   = (h - tw) / 2.0        # 4mm  socket x start (centred on h=12)
    ex   = sx + tw               # 8mm  socket x end

    # Right edge (x=h) with one base tab at y=l/2
    cy_tab = l / 2.0
    right = [
        (h, 0.0),
        (h, cy_tab - tw2), (h+t, cy_tab - tw2),
        (h+t, cy_tab + tw2), (h, cy_tab + tw2),
        (h, l),
    ]

    pts = [
        (0.0, 0.0),
        (sx,  0.0), (sx, t), (ex, t), (ex, 0.0),   # corner socket at top
        *right,                                       # right edge with base tab
        (0.0, l),
        # Z closes
    ]
    return pts, []


def _build_tc_tab(p: dict):
    """
    Short-wall end slice: shows corner tab (left side) + lid slot (top) + base tab (bottom).
    Width (x): 0..TC_SAMPLE_L (sample length along wall body direction).
    Height (y): 0..BOX_INTERIOR_H+MAT3.
    Corner tab protrudes left (x=-MAT3), centred on BOX_INTERIOR_H.
    Lid slot at y=0..BOX_DADO_W (open at top).
    Base tab at y=BOX_INTERIOR_H..BOX_INTERIOR_H+MAT3, centred on x.
    """
    l    = TC_SAMPLE_L           # 30mm  (along x)
    h    = p["BOX_INTERIOR_H"]   # 12mm
    t    = p["MAT3"]             # 3mm
    tw   = p["BOX_TAB_W"]        # 4mm
    tw2  = tw / 2.0
    dw   = p["BOX_DADO_W"]       # 3.2mm (lid slot depth from top)
    sy   = (h - tw) / 2.0        # 4mm   tab y start (centred on h=12)
    ey   = sy + tw               # 8mm   tab y end

    # Bottom edge (y=h) with one base tab centred on x
    cx_tab = l / 2.0
    bot = [
        (0.0, h),
        (cx_tab - tw2, h), (cx_tab - tw2, h+t),
        (cx_tab + tw2, h+t), (cx_tab + tw2, h),
        (l, h),
    ]

    pts = [
        (0.0, dw),                              # slot bottom-left (top slot open)
        (0.0, sy), (-t, sy), (-t, ey), (0.0, ey),   # corner tab (protrudes left)
        *bot,                                    # bottom edge with base tab
        (l, ey), (l, sy),                        # right face (no tab on right side)
        (l, dw),                                 # back to top-right
        # Z closes to (0.0, dw)
    ]
    return pts, []


def _build_tc_base_notch(p: dict):
    """
    Base edge strip: a flat strip with ONE edge notch at x=0 end.
    Tests wall-base tab fit: the tc_socket base tab slots into this notch.
    Dimensions: TC_SAMPLE_L × (MAT3 + 6mm) wide.
    Notch at x=0: 4mm wide × MAT3 deep, centred on width.
    """
    l    = TC_SAMPLE_L           # 30mm (strip length)
    nd   = p["MAT3"]             # 3mm  notch depth
    tw2  = p["BOX_TAB_W"] / 2.0  # 2mm  half-width
    w    = nd + 6.0              # 9mm  strip width (notch depth + 6mm margin)
    cy   = w / 2.0               # centre of strip width

    pts = [
        (0.0, 0.0),
        (0.0, cy - tw2), (nd, cy - tw2), (nd, cy + tw2), (0.0, cy + tw2),   # notch
        (0.0, w),
        (l,   w),
        (l,   0.0),
        # Z closes
    ]
    return pts, []


def _build_tc_lid(p: dict):
    """
    Lid gauge strip: a strip MAT3 thick × TC_SAMPLE_L long.
    Should slide into the tc_lid_slot top slot (BOX_DADO_W=3.2mm).
    """
    from src.geometry import rect_pts
    pts = rect_pts(0.0, 0.0, TC_SAMPLE_L, p["MAT3"])
    return pts, []


def _build_tc_lid_slot(p: dict):
    """
    Short-wall top: shows lid slot (BOX_DADO_W deep) in isolation.
    Width: BOX_INTERIOR_H + MAT3 (full cross-section with base tab).
    Height: TC_SAMPLE_L.
    Lid slot open at y=0..BOX_DADO_W (full width).
    Base tab at x=h..h+MAT3, centred on y.
    """
    h    = p["BOX_INTERIOR_H"]
    l    = TC_SAMPLE_L
    t    = p["MAT3"]
    tw   = p["BOX_TAB_W"]
    tw2  = tw / 2.0
    dw   = p["BOX_DADO_W"]

    cy_tab = l / 2.0
    right = [
        (h, 0.0),
        (h, cy_tab - tw2), (h+t, cy_tab - tw2),
        (h+t, cy_tab + tw2), (h, cy_tab + tw2),
        (h, l),
    ]

    pts = [
        (0.0, dw),               # lid slot: open at top, starts at dw
        *right,
        (0.0, l),
        # Z closes to (0.0, dw)
    ]
    return pts, []


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout(p: dict) -> list:
    """
    Place all test pieces on the TC_SHEET_W × TC_SHEET_H mm scrap sheet.
    Returns list of dicts: { 'id', 'label', 'local_pts', 'sheet_pts',
                              'sheet_holes', 'bbox' }
    """
    M = p["MARGIN"]
    G = 2.0

    pieces_local = [
        ("tc_socket",     *_build_tc_socket(p),     "CORNER SOCKET"),
        ("tc_tab",        *_build_tc_tab(p),         "CORNER TAB"),
        ("tc_base_notch", *_build_tc_base_notch(p),  "BASE NOTCH"),
        ("tc_lid",        *_build_tc_lid(p),         "LID STRIP"),
        ("tc_lid_slot",   *_build_tc_lid_slot(p),    "LID SLOT"),
    ]

    # Compute local bboxes to determine positions
    local_bbs = {}
    for pid, pts, holes, label in pieces_local:
        local_bbs[pid] = bounding_box(pts)

    h    = p["BOX_INTERIOR_H"]     # 12mm
    t    = p["MAT3"]               # 3mm
    dw   = p["BOX_DADO_W"]         # 3.2mm

    # tc_socket: bbox = (0, 0, h+t, l) = (0, 0, 15, 30)
    # tc_tab:    bbox = (-t, dw, l, h+t) = (-3, 3.2, 30, 15) → width=33, height=11.8
    # tc_base_notch: bbox = (0, 0, l, nd+6) = (0, 0, 30, 9)
    # tc_lid:    bbox = (0, 0, l, t) = (0, 0, 30, 3)
    # tc_lid_slot: bbox = (0, dw, h+t, l) = (0, 3.2, 15, 30)

    # Layout: two rows
    # Row 1 (y=M): tc_socket (15×30), tc_tab (33×~12), tc_lid_slot (15×30)
    # Row 2 (y=M+30+G): tc_base_notch (30×9), tc_lid (30×3)

    x_socket   = M
    x_tab      = x_socket + (local_bbs["tc_socket"][2] - local_bbs["tc_socket"][0]) + G
    x_lid_slot = x_tab    + (local_bbs["tc_tab"][2]    - local_bbs["tc_tab"][0])    + G

    y_row1 = M
    y_row2 = y_row1 + (local_bbs["tc_socket"][3] - local_bbs["tc_socket"][1]) + G

    x_notch = M
    x_lid   = x_notch + (local_bbs["tc_base_notch"][2] - local_bbs["tc_base_notch"][0]) + G

    positions = {
        "tc_socket":     (x_socket,   y_row1),
        "tc_tab":        (x_tab,      y_row1),
        "tc_lid_slot":   (x_lid_slot, y_row1),
        "tc_base_notch": (x_notch,    y_row2),
        "tc_lid":        (x_lid,      y_row2),
    }

    placed = []
    for pid, local_pts, local_holes, label in pieces_local:
        sx, sy = positions[pid]
        sheet_pts, sheet_holes = place(local_pts, local_holes, sx, sy)
        bb = bounding_box(sheet_pts)
        placed.append({
            "id":          pid,
            "label":       label,
            "local_pts":   local_pts,
            "sheet_pts":   sheet_pts,
            "sheet_holes": sheet_holes,
            "bbox":        bb,
        })

    # Validate bounds
    for part in placed:
        x0, y0, x1, y1 = part["bbox"]
        if x1 > TC_SHEET_W - M + 1e-6 or y1 > TC_SHEET_H - M + 1e-6:
            raise ValueError(
                f"tc piece '{part['id']}' out of bounds: "
                f"({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) on {TC_SHEET_W}×{TC_SHEET_H}"
            )

    return placed


# ---------------------------------------------------------------------------
# Render / generate
# ---------------------------------------------------------------------------

def render(placed: list, p: dict) -> str:
    lines = [
        svg_open(TC_SHEET_W, TC_SHEET_H,
                 "TEST CUT | 3mm SCRAP | Cut before full box sheet | "
                 "RED=CUT preview 0.1mm"),
        "",
    ]
    for part in placed:
        pid   = part["id"]
        pts   = part["sheet_pts"]
        bb    = part["bbox"]
        cx    = (bb[0] + bb[2]) / 2.0
        cy    = (bb[1] + bb[3]) / 2.0
        children = [
            cut_path(pts_to_path(pts), id_=f"{pid}_outer"),
            etch_text(cx, cy, part["label"], size=3.0),
        ]
        lines.append(svg_group(pid, children))
        lines.append("")
    lines.append(svg_close())
    return "\n".join(lines)


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
    svg = generate(p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


if __name__ == "__main__":
    path = write()
    print(f"Written: {path}")
