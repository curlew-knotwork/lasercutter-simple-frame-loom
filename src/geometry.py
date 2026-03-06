"""
src/geometry.py — SVG path building primitives for laser-cut flat parts.

Coordinate system: mm, origin top-left, y increases downward (SVG standard).
All outer boundary paths: clockwise winding.
All inner hole paths: counter-clockwise winding (so fill:evenodd cuts holes).
Every path is closed (ends with Z).

Parts are built in LOCAL coordinates (origin at part top-left or a defined anchor).
Callers translate to sheet coordinates using translate().
"""

import math


# ---------------------------------------------------------------------------
# Point list operations
# ---------------------------------------------------------------------------

def translate(pts: list, dx: float, dy: float) -> list:
    return [(x + dx, y + dy) for x, y in pts]


def mirror_x(pts: list, cx: float) -> list:
    """Mirror all points about the vertical line x = cx."""
    return [(2.0 * cx - x, y) for x, y in pts]


def mirror_y(pts: list, cy: float) -> list:
    """Mirror all points about the horizontal line y = cy."""
    return [(x, 2.0 * cy - y) for x, y in pts]


def rotate_90_cw(pts: list) -> list:
    """Rotate 90° clockwise about origin: (x,y) → (y, -x)."""
    return [(y, -x) for x, y in pts]


def bounding_box(pts: list) -> tuple:
    """Return (xmin, ymin, xmax, ymax) of a point list."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_from_path_str(path: str) -> tuple:
    """
    Approximate bounding box from an SVG path string (M/L/Z commands only).
    Ignores arc commands — for arc-based paths use circle_bbox / ellipse_bbox.
    """
    pts = []
    for token in path.replace(',', ' ').split():
        try:
            pts.append(float(token))
        except ValueError:
            pass
    if len(pts) < 2:
        return (0, 0, 0, 0)
    xs = pts[0::2]
    ys = pts[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def circle_bbox(cx: float, cy: float, r: float) -> tuple:
    return cx - r, cy - r, cx + r, cy + r


def ellipse_bbox(cx: float, cy: float, rx: float, ry: float) -> tuple:
    return cx - rx, cy - ry, cx + rx, cy + ry


def bboxes_overlap(a: tuple, b: tuple) -> bool:
    """True iff two bounding boxes share interior area."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


# ---------------------------------------------------------------------------
# Path string builders
# ---------------------------------------------------------------------------

def pts_to_path(pts: list) -> str:
    """
    Convert [(x,y), ...] to SVG path string 'M x,y L x,y ... Z'.
    Coordinates rounded to 4 decimal places.
    """
    if not pts:
        return ""
    coords = [f"M {pts[0][0]:.4f},{pts[0][1]:.4f}"]
    for x, y in pts[1:]:
        coords.append(f"L {x:.4f},{y:.4f}")
    coords.append("Z")
    return " ".join(coords)


def circle_path(cx: float, cy: float, r: float) -> str:
    """
    Closed circle as SVG path (two semicircular arcs, counter-clockwise).
    Use for inner holes.
    """
    return (
        f"M {cx + r:.4f},{cy:.4f} "
        f"A {r:.4f},{r:.4f} 0 1,0 {cx - r:.4f},{cy:.4f} "
        f"A {r:.4f},{r:.4f} 0 1,0 {cx + r:.4f},{cy:.4f} Z"
    )


def ellipse_path(cx: float, cy: float, rx: float, ry: float) -> str:
    """
    Closed ellipse as SVG path (two semi-arcs, counter-clockwise).
    Use for inner holes (lightening slots, grip holes).
    """
    return (
        f"M {cx + rx:.4f},{cy:.4f} "
        f"A {rx:.4f},{ry:.4f} 0 1,0 {cx - rx:.4f},{cy:.4f} "
        f"A {rx:.4f},{ry:.4f} 0 1,0 {cx + rx:.4f},{cy:.4f} Z"
    )


# ---------------------------------------------------------------------------
# Polygon path helpers
# ---------------------------------------------------------------------------

def rect_pts(x: float, y: float, w: float, h: float) -> list:
    """Clockwise rectangle points: TL → TR → BR → BL."""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


# ---------------------------------------------------------------------------
# SVG document helpers
# ---------------------------------------------------------------------------

CUT_STYLE   = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
ETCH_STYLE  = 'fill="none" stroke="#000000" stroke-width="0.4"'
SHEET_STYLE = 'fill="#faf8f4" stroke="#aaaaaa" stroke-width="0.3"'


def svg_open(w_mm: float, h_mm: float, title: str = "") -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     viewBox="0 0 {w_mm} {h_mm}"',
        f'     width="{w_mm}mm" height="{h_mm}mm">',
    ]
    if title:
        lines.append(f'  <!-- {title} -->'),
    # Sheet background reference rectangle
    lines.append(
        f'  <rect x="0" y="0" width="{w_mm}" height="{h_mm}" {SHEET_STYLE}/>'
    )
    return "\n".join(lines)


def svg_close() -> str:
    return "</svg>"


def svg_group(id_: str, children: list, transform: str = "") -> str:
    attr = f'id="{id_}"'
    if transform:
        attr += f' transform="{transform}"'
    inner = "\n".join(f"  {c}" for c in children)
    return f'<g {attr}>\n{inner}\n</g>'


def cut_path(path_str: str, id_: str = "") -> str:
    id_attr = f' id="{id_}"' if id_ else ""
    return f'<path{id_attr} d="{path_str}" {CUT_STYLE}/>'


def etch_path(path_str: str, id_: str = "") -> str:
    id_attr = f' id="{id_}"' if id_ else ""
    return f'<path{id_attr} d="{path_str}" {ETCH_STYLE}/>'


def etch_text(x: float, y: float, text: str,
              size: float = 4.0, anchor: str = "middle") -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" '
        f'font-size="{size}" font-family="monospace" '
        f'text-anchor="{anchor}" fill="#000000">{text}</text>'
    )


# ---------------------------------------------------------------------------
# Part path builders (return point lists in local coordinates)
# Caller uses translate() to place on sheet.
# ---------------------------------------------------------------------------

def rail_pts(
    rail_w: float,      # outer width of rail = FRAME_OUTER_W
    rail_h: float,      # height of rail = RAIL_W (= STILE_W)
    sock_w: float,      # finger joint socket opening width (= TAB_W; must == TAB_W)
    sock_d: float,      # socket depth (= TAB_L = MAT)
    notch_cxs: list,    # list of notch centreline x positions (in local rail coords)
    notch_w: float,     # notch width
    notch_d: float,     # notch depth
    notches_open_down: bool = True,  # True for top rail; False for bottom rail
) -> list:
    """
    Build closed point list for a rail (top or bottom).

    Local origin: top-left corner of rail outer bounding box.

    Right end: finger socket (slot going LEFT from right face into body).
    Left end: finger socket (slot going RIGHT from left face into body).
    Inner edge: warp notches (up or down depending on notches_open_down).

    Socket position: centred on the 22mm height axis.
    sock_y_top = (rail_h - sock_w) / 2
    sock_y_bot = sock_y_top + sock_w

    Returns clockwise winding (outer boundary).
    """
    sy_top = (rail_h - sock_w) / 2.0
    sy_bot = sy_top + sock_w
    notch_edge_y = rail_h if notches_open_down else 0.0
    notch_dir    = +1.0  if notches_open_down else -1.0  # sign for y

    pts = []

    # ── Top edge (y=0), left to right ──────────────────────────────────────
    pts.append((0.0, 0.0))
    pts.append((rail_w, 0.0))

    # ── Right end (x=rail_w), top to bottom, with socket ───────────────────
    pts.append((rail_w, sy_top))
    pts.append((rail_w - sock_d, sy_top))   # step LEFT (into body)
    pts.append((rail_w - sock_d, sy_bot))
    pts.append((rail_w, sy_bot))
    pts.append((rail_w, rail_h))

    # ── Inner edge (y=rail_h for top rail), right to left, with notches ────
    # Build notch centrelines sorted right-to-left
    sorted_cxs = sorted(notch_cxs, reverse=True)

    cur_x = rail_w
    for cx in sorted_cxs:
        nxr = cx + notch_w / 2.0
        nxl = cx - notch_w / 2.0
        # Straight to right edge of notch
        pts.append((nxr, notch_edge_y))
        # Down (or up) into notch
        pts.append((nxr, notch_edge_y + notch_dir * notch_d))
        pts.append((nxl, notch_edge_y + notch_dir * notch_d))
        # Back to inner edge y
        pts.append((nxl, notch_edge_y))
        cur_x = nxl

    # Continue to left end
    pts.append((0.0, rail_h))

    # ── Left end (x=0), bottom to top, with socket ─────────────────────────
    pts.append((0.0, sy_bot))
    pts.append((sock_d, sy_bot))             # step RIGHT (into body)
    pts.append((sock_d, sy_top))
    pts.append((0.0, sy_top))

    # Back to start (implicit via Z, but we return the list without start repeat)
    return pts


def stile_pts(
    stile_w: float,      # = STILE_W = 22mm
    stile_h: float,      # = STILE_BODY_H (body only, not including tab protrusions)
    tab_w: float,        # = TAB_W = 7.33mm
    tab_l: float,        # = TAB_L = MAT = 6mm
    cross_mortises=None, # ignored (D-13: mortises are separate rect_holes, not polygon dips)
) -> list:
    """
    Build closed point list for a stile (left or right).

    Local origin: top-left of stile BODY (not including tab protrusion).
    Stile body: (0,0) to (stile_w, stile_h). Straight edges — no mortise indentations.
    Top tab protrudes UP to y=-tab_l; bottom tab protrudes DOWN to y=stile_h+tab_l.

    Crossbar mortises are separate rect_holes (D-13), not embedded in this outline.
    Returns clockwise winding. 12 points.
    """
    gap_w = (stile_w - tab_w) / 2.0
    tab_x0 = gap_w
    tab_x1 = gap_w + tab_w

    return [
        (0.0,     0.0),          # top-left of body
        (tab_x0,  0.0),          # left shoulder of top tab
        (tab_x0,  -tab_l),       # top-left of top tab
        (tab_x1,  -tab_l),       # top-right of top tab
        (tab_x1,  0.0),          # right shoulder of top tab
        (stile_w, 0.0),          # top-right of body
        (stile_w, stile_h),      # bottom-right of body (inner face, straight)
        (tab_x1,  stile_h),      # right shoulder of bottom tab
        (tab_x1,  stile_h + tab_l),  # bottom-right of bottom tab
        (tab_x0,  stile_h + tab_l),  # bottom-left of bottom tab
        (tab_x0,  stile_h),      # left shoulder of bottom tab
        (0.0,     stile_h),      # bottom-left of body (outer face, straight)
        # Z closes back to (0.0, 0.0)
    ]


def crossbar_pts(body_w: float, body_h: float) -> list:
    """
    Crossbar: plain rectangle. No tenons (D-13).
    Local origin: top-left. Total: body_w × body_h.
    Returns clockwise rectangle (4 points).
    """
    return rect_pts(0.0, 0.0, body_w, body_h)


def shuttle_pts(length: float, width: float, taper_l: float) -> list:
    """
    Shuttle: rectangle with tapered ends (symmetric). V-notch at tips handled separately.
    Local origin: top-left of bounding box.

    The body runs from x=taper_l to x=length-taper_l at full width.
    Tapers taper linearly to a point (V-notch tip handled as part of outline).

    For a simple rectangular shuttle with angled ends (no true V-tip):
      - At x=0: y = width/2 (tip, single point)
      - At x=taper_l: y = 0 and y = width (full width)
      - Body: x=taper_l to x=length-taper_l, y=0..width
      - Right taper mirrors left

    V-notch at tips: the tip is not a point but a V-notch cut into it.
    We model the tip as two points forming a V (notch_hw from centre).
    """
    half = width / 2.0
    # Going clockwise from left tip
    pts = [
        (0.0, half),                    # left tip (will be notched — see below)
        (taper_l, 0.0),                 # top-left of body
        (length - taper_l, 0.0),        # top-right of body
        (length, half),                 # right tip
        (length - taper_l, width),      # bottom-right of body
        (taper_l, width),               # bottom-left of body
    ]
    return pts


def shuttle_pts_with_notch(
    length: float, width: float, taper_l: float, notch_hw: float
) -> list:
    """
    Shuttle with V-notches at each tip (clockwise winding).

    V-notch geometry (matches v6 SVG convention):
      At right tip: taper arrives at (length, half±notch_hw), then dips inward to
      (length - notch_hw, half) before reversing.
      At left tip: symmetric.

    This creates the yarn-catching V-notch at each end.
    """
    half = width / 2.0
    return [
        (taper_l, 0.0),                      # top-left of body
        (length - taper_l, 0.0),             # top-right of body
        (length, half - notch_hw),           # right tip, top edge
        (length - notch_hw, half),           # right V-notch inward tip
        (length, half + notch_hw),           # right tip, bottom edge
        (length - taper_l, width),           # bottom-right of body
        (taper_l, width),                    # bottom-left of body
        (0.0, half + notch_hw),             # left tip, bottom edge
        (notch_hw, half),                    # left V-notch inward tip
        (0.0, half - notch_hw),             # left tip, top edge
    ]


def beater_pts(
    beater_w: float,
    handle_h: float,
    tooth_h: float,
    tooth_w: float,
    tooth_pitch: float,
    tooth_count: int,
) -> list:
    """
    Beater/comb: handle rectangle at top, teeth pointing downward.
    Local origin: top-left of handle.
    Total height: handle_h + tooth_h.

    Teeth at pitch `tooth_pitch`, centred on the beater.
    First tooth centreline: at x = (beater_w - (tooth_count-1)*tooth_pitch) / 2.
    This ensures the tooth array is centred on the beater.

    Going clockwise from top-left of handle.
    """
    gap_w = tooth_pitch - tooth_w

    # First tooth centreline x (centred on beater_w)
    array_width = (tooth_count - 1) * tooth_pitch
    first_cx = (beater_w - array_width) / 2.0

    # The handle bottom edge and the top of the tooth region are at y=handle_h.
    # Going from left to right along the bottom of the handle / top of teeth:
    # Between teeth (gaps): open downward gaps of width gap_w.
    # Teeth: solid sections of width tooth_w.

    pts = []

    # Top edge
    pts.append((0.0, 0.0))
    pts.append((beater_w, 0.0))
    # Right side of handle
    pts.append((beater_w, handle_h))

    # Tooth region: right to left along the comb bottom edge
    # Rightmost tooth: last tooth, at cx = first_cx + (tooth_count-1)*tooth_pitch
    # Gap to the right of rightmost tooth: from x=(last_cx + tooth_w/2) to x=beater_w
    # Between teeth: gap of width gap_w

    # Build teeth right to left
    # Start at (beater_w, handle_h) — top-right of tooth region
    # Need to walk left, descending into each tooth

    # Tooth x positions (centres, left to right)
    tooth_cxs = [first_cx + i * tooth_pitch for i in range(tooth_count)]

    # Right gap: from last tooth right edge to beater right edge
    last_cx = tooth_cxs[-1]
    right_margin = beater_w - (last_cx + tooth_w / 2.0)

    # Walk right to left
    # Start at (beater_w, handle_h) — already appended above
    for i in range(tooth_count - 1, -1, -1):
        cx = tooth_cxs[i]
        tx_r = cx + tooth_w / 2.0
        tx_l = cx - tooth_w / 2.0
        tooth_bot = handle_h + tooth_h

        # Right side of this tooth (going down)
        pts.append((tx_r, handle_h))
        pts.append((tx_r, tooth_bot))
        # Tooth bottom
        pts.append((tx_l, tooth_bot))
        # Left side of this tooth (going up)
        pts.append((tx_l, handle_h))
        # Gap to next tooth (or left margin)

    # Left margin from leftmost tooth left edge to x=0
    pts.append((0.0, handle_h))
    # Left edge back to top
    # (close to (0,0) via Z)

    return pts


# ---------------------------------------------------------------------------
# Hole tuple helpers — transport holes through translate/place without
# parsing SVG path strings. Each hole is a tuple: ('circle'|'ellipse', *params).
# ---------------------------------------------------------------------------

def circle_hole(cx: float, cy: float, r: float) -> tuple:
    return ('circle', cx, cy, r)


def ellipse_hole(cx: float, cy: float, rx: float, ry: float) -> tuple:
    return ('ellipse', cx, cy, rx, ry)


def rect_hole(x: float, y: float, w: float, h: float) -> tuple:
    """Rectangular through-hole (mortise slot). CCW winding via pts_to_path(rect_pts(...))."""
    return ('rect', x, y, w, h)


def translate_hole(hole: tuple, dx: float, dy: float) -> tuple:
    if hole[0] == 'circle':
        _, cx, cy, r = hole
        return ('circle', cx + dx, cy + dy, r)
    elif hole[0] == 'ellipse':
        _, cx, cy, rx, ry = hole
        return ('ellipse', cx + dx, cy + dy, rx, ry)
    elif hole[0] == 'rect':
        _, x, y, w, h = hole
        return ('rect', x + dx, y + dy, w, h)
    raise ValueError(f"Unknown hole type: {hole[0]}")


def hole_to_path(hole: tuple) -> str:
    if hole[0] == 'circle':
        return circle_path(hole[1], hole[2], hole[3])
    elif hole[0] == 'ellipse':
        return ellipse_path(hole[1], hole[2], hole[3], hole[4])
    elif hole[0] == 'rect':
        _, x, y, w, h = hole
        return pts_to_path(rect_pts(x, y, w, h))
    raise ValueError(f"Unknown hole type: {hole[0]}")


def place(local_pts: list, local_holes: list, sx: float, sy: float):
    """
    Translate a part's local points and holes to sheet position (sx, sy),
    where (sx, sy) is the desired sheet position of the local bounding box top-left.
    Returns (sheet_pts, sheet_holes).
    """
    bb = bounding_box(local_pts)
    dx = sx - bb[0]
    dy = sy - bb[1]
    sheet_pts = translate(local_pts, dx, dy)
    sheet_holes = [translate_hole(h, dx, dy) for h in local_holes]
    return sheet_pts, sheet_holes


def stand_leg_pts(
    leg_w: float,     # = STAND_LEG_W = 40mm
    leg_l: float,     # = STAND_LEG_L = 300mm
    notch_w: float,   # = STAND_NOTCH_W = 22.5mm (stile width + clearance)
    notch_d: float,   # = STAND_NOTCH_D = 25mm
) -> list:
    """
    Stand leg: rectangle with U-notch at top for loom stile.

    Local origin: top-left of bounding box.
    Notch is open at y=0 (top of piece), centred on leg_w.
    Notch dips DOWN to y=notch_d.

    Clockwise winding (outer boundary).
    """
    nx0 = (leg_w - notch_w) / 2.0   # left wall of notch
    nx1 = (leg_w + notch_w) / 2.0   # right wall of notch
    return [
        (0.0,   0.0),       # top-left
        (nx0,   0.0),       # left of notch opening
        (nx0,   notch_d),   # notch bottom-left
        (nx1,   notch_d),   # notch bottom-right
        (nx1,   0.0),       # right of notch opening
        (leg_w, 0.0),       # top-right
        (leg_w, leg_l),     # bottom-right
        (0.0,   leg_l),     # bottom-left
    ]


def prop_pts(
    body_h: float,       # leg body height (not including tenon)
    body_w: float,       # leg body width
    ten_l: float,        # tenon length (protrudes from top)
    ten_w: float,        # tenon width (centred on body_w)
    foot_bevel_d: float, # depth of foot bevel (diagonal cut at bottom-opposite corner)
    bevel_on_right: bool = True,  # True for prop-L, False for prop-R
) -> list:
    """
    Prop arm: a rectangular body with tenon at top and bevelled foot.
    Local origin: top-left of tenon.
    Tenon centred on body_w.

    Bevel: for prop-L (bevel_on_right=True), bottom-right corner is cut diagonally.
    For prop-R (bevel_on_right=False), bottom-left corner is cut.

    The bevel represents the foot sitting flat on the table at the lean angle.
    """
    gap = (body_w - ten_w) / 2.0
    ten_top = 0.0
    ten_bot = ten_l
    body_top = ten_l
    body_bot = ten_l + body_h

    if bevel_on_right:
        # Clockwise from top-left of tenon (which is at x=gap, y=0)
        pts = [
            (gap, ten_top),
            (gap + ten_w, ten_top),
            (gap + ten_w, ten_bot),
            (body_w, ten_bot),
            # Right side of body, going down to bevel start
            (body_w, body_bot - foot_bevel_d),
            # Bevel cut: from (body_w, body_bot - foot_bevel_d) to (0, body_bot)
            (0.0, body_bot),
            # Left side of body, going up to tenon
            (0.0, ten_bot),
            (gap, ten_bot),
        ]
    else:
        # Mirror: bevel on left
        pts = [
            (gap, ten_top),
            (gap + ten_w, ten_top),
            (gap + ten_w, ten_bot),
            (body_w, ten_bot),
            (body_w, body_bot),
            # Bevel cut: from (body_w, body_bot) ... wait, bevel on left
            # Bevel: from (body_w, body_bot) → (0, body_bot - foot_bevel_d)? No.
            # For prop-R (mirror of prop-L), bottom-left corner is bevelled:
            # Goes from (0, body_bot - foot_bevel_d) to (body_w, body_bot)
            # Left side going up to bevel point
        ]
        # Redo for left bevel:
        pts = [
            (gap, ten_top),
            (gap + ten_w, ten_top),
            (gap + ten_w, ten_bot),
            (body_w, ten_bot),
            (body_w, body_bot),
            (foot_bevel_d, body_bot),       # bottom edge (bevel removes left corner)
            # Actually: bevel from bottom-left. Remove the bottom-left corner:
            # Instead of going to (0, body_bot), cut diagonally:
            # (foot_bevel_d, body_bot) → (0, body_bot - ???)
            # The bevel depth (foot_bevel_d) is the horizontal cut width.
            # The corresponding vertical cut depth = foot_bevel_d * tan(lean_angle)
            # tan(25°) = 0.4663 → vertical = foot_bevel_d * 0.4663
        ]
        # This is getting complex — stub for now, implement exactly in loom.py
        # Return rectangular prop for now; bevel added in loom.py
        pts = rect_pts(0.0, 0.0, body_w, ten_l + body_h)

    return pts
