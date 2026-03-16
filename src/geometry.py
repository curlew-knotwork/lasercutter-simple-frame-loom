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


def stadium_path(cx: float, cy: float, r: float, h: float) -> str:
    """
    Closed vertical stadium (two semicircles + straight sides) as SVG path.
    r = semicircle radius, h = total height (must be >= 2r), width = 2r.

    SVG arc direction (y-down coords), sweep=0 for both caps:
      Top cap  (right→left, θ: 0→π CCW): sweep=0 → goes through y=top_cy-r (above) ✓
      Bottom cap (left→right, θ: π→0 CCW): sweep=0 → goes through y=bot_cy+r (below) ✓

    sweep=1 for either cap produces an inward (concave) arc. Use sweep=0 for both.
    Use for inner holes.
    """
    h_rect = h - 2.0 * r
    top_cy = cy - h_rect / 2.0
    bot_cy = cy + h_rect / 2.0
    return (
        f"M {cx + r:.4f},{top_cy:.4f} "
        f"A {r:.4f},{r:.4f} 0 1,0 {cx - r:.4f},{top_cy:.4f} "
        f"L {cx - r:.4f},{bot_cy:.4f} "
        f"A {r:.4f},{r:.4f} 0 1,0 {cx + r:.4f},{bot_cy:.4f} "
        f"Z"
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

CUT_STYLE   = 'fill="none" stroke="#ff0000" stroke-width="0.3"'
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
    rail_w: float,          # outer width of rail = FRAME_OUTER_W
    rail_h: float,          # height of rail = RAIL_W (= STILE_W)
    sock_w: float,          # finger joint socket opening width (= TAB_W)
    sock_d: float,          # socket depth (= TAB_L = MAT)
    notch_cxs: list,        # list of notch centreline x positions (in local rail coords)
    notch_w: float,         # notch width
    notch_d: float,         # notch depth
    notches_open_down: bool = True,   # True for top rail; False for bottom rail
    stand_tab_l: float = 0.0,         # D-17: stand tab extension past each stile face (top rail only)
) -> list:
    """
    Build closed point list for a rail (top or bottom).

    Local origin: top-left corner of bounding box.
    When stand_tab_l > 0, the bbox is (-stand_tab_l, 0, rail_w+stand_tab_l, rail_h).

    Right end: stile finger socket at x=rail_w (step LEFT by sock_d), centred on rail_h.
    Left end: stile finger socket at x=0 (step RIGHT by sock_d), centred on rail_h.
    With stand_tab_l > 0: stand tab protrudes an additional stand_tab_l beyond each end,
    connected to the socket via horizontal ledges at the socket y limits — E-shape ends.

    Inner edge: warp notches (open direction depends on notches_open_down).
    Returns clockwise winding (outer boundary).
    """
    sy_top = (rail_h - sock_w) / 2.0
    sy_bot = sy_top + sock_w
    notch_edge_y = rail_h if notches_open_down else 0.0
    notch_dir    = +1.0  if notches_open_down else -1.0

    pts = []

    if stand_tab_l <= 0.0:
        # ── No stand tabs — original geometry ────────────────────────────
        pts.append((0.0, 0.0))
        pts.append((rail_w, 0.0))
        pts.append((rail_w, sy_top))
        pts.append((rail_w - sock_d, sy_top))
        pts.append((rail_w - sock_d, sy_bot))
        pts.append((rail_w, sy_bot))
        pts.append((rail_w, rail_h))
    else:
        # ── Right stand tab + socket (E-shape end) ────────────────────────
        # Start at bounding-box top-left, go right across full width
        pts.append((-stand_tab_l, 0.0))
        pts.append((rail_w + stand_tab_l, 0.0))
        # Right stand tab: down to socket top ledge
        pts.append((rail_w + stand_tab_l, sy_top))
        # Ledge left to socket face
        pts.append((rail_w, sy_top))
        # Socket carved left by sock_d
        pts.append((rail_w - sock_d, sy_top))
        pts.append((rail_w - sock_d, sy_bot))
        pts.append((rail_w, sy_bot))
        # Ledge right back to stand tab face
        pts.append((rail_w + stand_tab_l, sy_bot))
        # Down to bottom of stand tab
        pts.append((rail_w + stand_tab_l, rail_h))
        # Return to rail body bottom-right
        pts.append((rail_w, rail_h))

    # ── Inner edge, right to left, with notches ───────────────────────────
    for cx in sorted(notch_cxs, reverse=True):
        nxr = cx + notch_w / 2.0
        nxl = cx - notch_w / 2.0
        pts.append((nxr, notch_edge_y))
        pts.append((nxr, notch_edge_y + notch_dir * notch_d))
        pts.append((nxl, notch_edge_y + notch_dir * notch_d))
        pts.append((nxl, notch_edge_y))

    # ── Left end ──────────────────────────────────────────────────────────
    if stand_tab_l <= 0.0:
        pts.append((0.0, rail_h))
        pts.append((0.0, sy_bot))
        pts.append((sock_d, sy_bot))
        pts.append((sock_d, sy_top))
        pts.append((0.0, sy_top))
    else:
        # Left body bottom, then left stand tab + socket (E-shape, mirrored)
        pts.append((0.0, rail_h))
        pts.append((-stand_tab_l, rail_h))
        # Up to socket bottom ledge
        pts.append((-stand_tab_l, sy_bot))
        # Ledge right to socket face
        pts.append((0.0, sy_bot))
        # Socket carved right by sock_d
        pts.append((sock_d, sy_bot))
        pts.append((sock_d, sy_top))
        pts.append((0.0, sy_top))
        # Ledge left back to stand tab face
        pts.append((-stand_tab_l, sy_top))
        # Up to top of stand tab (close to start via Z)

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
    first_cx: float = None,
) -> list:
    """
    Beater/comb: handle rectangle at top, teeth pointing downward.
    Local origin: top-left of handle.
    Total height: handle_h + tooth_h.

    first_cx: local x of first tooth centreline. If None, centres array on beater_w.
    Pass BEATER_FIRST_CX from params for alignment-correct positioning (D-35).

    Going clockwise from top-left of handle.
    """
    gap_w = tooth_pitch - tooth_w

    # First tooth centreline x
    if first_cx is None:
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
# Rounded-corner path builders (D-25)
#
# rail_path() and beater_path() return SVG path strings with quarter-circle
# fillets at notch/tooth corners.  Sweep direction from cross-product rule:
#   z = dx_in * dy_out − dy_in * dx_out
#   z > 0 → sweep=0,  z < 0 → sweep=1
# ox, oy: sheet-coordinate offset applied to all coordinates.
# ---------------------------------------------------------------------------

def _arc(r: float, sweep: int, ex: float, ey: float) -> str:
    return f"A {r:.4f},{r:.4f} 0 0,{sweep} {ex:.4f},{ey:.4f}"


def rounded_pts_to_path(
    pts: list,
    corner_r: float,
    radii: list = None,
    ox: float = 0.0,
    oy: float = 0.0,
) -> str:
    """
    Build a closed SVG path from a polygon point list with quarter-circle fillets
    at every corner (D-25/D-26).

    corner_r: uniform radius applied to all corners when radii=None.
    radii: per-corner list of floats (len == len(pts)). Overrides corner_r per corner.
           r=0 for a corner → emit L directly to corner point (no setback, no arc).

    Sweep direction from cross-product rule:
      z = dx_in * dy_out - dy_in * dx_out
      z > 0 → sweep=0,  z < 0 → sweep=1

    M starts at departure of corners[0]; path ends with the arc of corners[0] then Z.
    ox, oy: sheet-coordinate offset applied to all coordinates.
    """
    n = len(pts)
    r_list = radii if radii is not None else [corner_r] * n

    if all(r == 0.0 for r in r_list):
        shifted = translate(pts, ox, oy) if (ox or oy) else pts
        return pts_to_path(shifted)

    def P(x, y):
        return f"{x + ox:.4f},{y + oy:.4f}"

    def unit(a, b):
        dx = b[0] - a[0]; dy = b[1] - a[1]
        d = math.sqrt(dx * dx + dy * dy)
        return (dx / d, dy / d) if d > 1e-12 else (1.0, 0.0)

    # Precompute approach, departure, sweep, radius for each corner
    corners = []
    for i in range(n):
        prev = pts[(i - 1) % n]
        curr = pts[i]
        next_ = pts[(i + 1) % n]
        r = r_list[i]
        if r == 0.0:
            corners.append((curr, curr, 0, 0.0))
        else:
            ux_in, uy_in = unit(prev, curr)
            ux_out, uy_out = unit(curr, next_)
            approach  = (curr[0] - r * ux_in,  curr[1] - r * uy_in)
            departure = (curr[0] + r * ux_out, curr[1] + r * uy_out)
            z = ux_in * uy_out - uy_in * ux_out
            sweep = 1 if z > 0 else 0
            corners.append((approach, departure, sweep, r))

    # Start at departure of corner 0; walk corners 1..n-1 then close with corner 0's arc
    segs = [f"M {P(*corners[0][1])}"]
    for i in list(range(1, n)) + [0]:
        approach, departure, sweep, r = corners[i]
        segs.append(f"L {P(*approach)}")
        if r > 0.0:
            segs.append(_arc(r, sweep, departure[0] + ox, departure[1] + oy))
    segs.append("Z")
    return " ".join(segs)


def shuttle_path(
    length: float,
    width: float,
    taper_l: float,
    notch_hw: float,
    corner_r: float = 0.0,
    ox: float = 0.0,
    oy: float = 0.0,
) -> str:
    """
    SVG path for a shuttle with fillets on tip/notch corners (D-26/D-28).

    Body/taper junctions (indices 0,1,5,6) use r=0 to prevent cookie-bite arcs
    at shallow taper angles (D-28). Only the 6 tip/notch corners are rounded.
    """
    pts = shuttle_pts_with_notch(length, width, taper_l, notch_hw)
    # Indices 0,1,5,6: body/taper junctions — r=0 (no setback, no arc)
    # Indices 2,3,4,7,8,9: tip and V-notch corners — r=corner_r
    radii = [0.0 if i in (0, 1, 5, 6) else corner_r for i in range(len(pts))]
    return rounded_pts_to_path(pts, corner_r, radii=radii, ox=ox, oy=oy)


def rail_path(
    rail_w: float,
    rail_h: float,
    sock_w: float,
    sock_d: float,
    notch_cxs: list,
    notch_w: float,
    notch_d: float,
    corner_r: float = 0.0,
    notches_open_down: bool = True,
    stand_tab_l: float = 0.0,
    ox: float = 0.0,
    oy: float = 0.0,
) -> str:
    """
    SVG path string for a rail, with optional quarter-circle fillets on all
    4 corners of every warp notch (D-25).  ox, oy shift to sheet coordinates.
    Only stand_tab_l=0 supported (current project has STAND_RAIL_TAB_L=0).
    """
    r = corner_r
    sy_top = (rail_h - sock_w) / 2.0
    sy_bot = sy_top + sock_w
    edge_y = rail_h if notches_open_down else 0.0
    d = notch_d if notches_open_down else -notch_d  # signed depth into notch

    def P(x, y):
        return f"{x + ox:.4f},{y + oy:.4f}"

    segs = [f"M {P(0.0, 0.0)}"]

    # ── Top edge ──────────────────────────────────────────────────────────
    segs.append(f"L {P(rail_w, 0.0)}")

    # ── Right socket (no rounding — joint surface) ────────────────────────
    segs.append(f"L {P(rail_w, sy_top)}")
    segs.append(f"L {P(rail_w - sock_d, sy_top)}")
    segs.append(f"L {P(rail_w - sock_d, sy_bot)}")
    segs.append(f"L {P(rail_w, sy_bot)}")
    segs.append(f"L {P(rail_w, rail_h)}")

    # ── Notch region: right to left ────────────────────────────────────────
    # Approach to first (rightmost) notch along rail edge
    for cx in sorted(notch_cxs, reverse=True):
        nxr = cx + notch_w / 2.0
        nxl = cx - notch_w / 2.0
        inner_y = edge_y + d   # y at notch floor (signed)

        if r == 0.0:
            # Sharp corners — match rail_pts() exactly
            segs.append(f"L {P(nxr, edge_y)}")
            segs.append(f"L {P(nxr, inner_y)}")
            segs.append(f"L {P(nxl, inner_y)}")
            segs.append(f"L {P(nxl, edge_y)}")
        else:
            # Outer right: incoming left(-1,0) → outgoing down(0,+d_sign)
            # z = (-1)*d_sign - 0*0 = -d_sign  → sweep=1 if d>0, sweep=0 if d<0
            sw_outer = 0 if d > 0 else 1
            sw_inner = 1 - sw_outer  # inner corners opposite

            # Outer right corner
            segs.append(f"L {P(nxr + r, edge_y)}")
            segs.append(_arc(r, sw_outer, *( (nxr + ox, edge_y + (d/abs(d))*r + oy) )))

            # Inner right corner
            segs.append(f"L {P(nxr, inner_y - (d/abs(d))*r)}")
            segs.append(_arc(r, sw_inner, *( (nxr - r + ox, inner_y + oy) )))

            # Inner left corner
            segs.append(f"L {P(nxl + r, inner_y)}")
            segs.append(_arc(r, sw_inner, *( (nxl + ox, inner_y - (d/abs(d))*r + oy) )))

            # Outer left corner
            segs.append(f"L {P(nxl, edge_y + (d/abs(d))*r)}")
            segs.append(_arc(r, sw_outer, *( (nxl - r + ox, edge_y + oy) )))

    # ── Left end ──────────────────────────────────────────────────────────
    segs.append(f"L {P(0.0, rail_h)}")
    segs.append(f"L {P(0.0, sy_bot)}")
    segs.append(f"L {P(sock_d, sy_bot)}")
    segs.append(f"L {P(sock_d, sy_top)}")
    segs.append(f"L {P(0.0, sy_top)}")
    segs.append("Z")

    return " ".join(segs)


def beater_path(
    beater_w: float,
    handle_h: float,
    tooth_h: float,
    tooth_w: float,
    tooth_pitch: float,
    tooth_count: int,
    corner_r: float = 0.0,
    ox: float = 0.0,
    oy: float = 0.0,
    first_cx: float = None,
) -> str:
    """
    SVG path string for a beater/comb with optional fillets on all corners (D-25/D-26).
    Rounds every corner: 4 handle corners + 4 per tooth gap = 4 + 4×tooth_count total.
    Pass first_cx=p["BEATER_FIRST_CX"] for alignment-correct tooth positioning (D-35).
    """
    pts = beater_pts(beater_w, handle_h, tooth_h, tooth_w, tooth_pitch, tooth_count,
                     first_cx=first_cx)
    return rounded_pts_to_path(pts, corner_r, ox=ox, oy=oy)


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


def stadium_hole(cx: float, cy: float, r: float, h: float) -> tuple:
    """Vertical stadium hole: two semicircles (radius r) + straight sides, total height h."""
    return ('stadium', cx, cy, r, h)


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
    elif hole[0] == 'stadium':
        _, cx, cy, r, h = hole
        return ('stadium', cx + dx, cy + dy, r, h)
    raise ValueError(f"Unknown hole type: {hole[0]}")


def hole_to_path(hole: tuple) -> str:
    if hole[0] == 'circle':
        return circle_path(hole[1], hole[2], hole[3])
    elif hole[0] == 'ellipse':
        return ellipse_path(hole[1], hole[2], hole[3], hole[4])
    elif hole[0] == 'rect':
        _, x, y, w, h = hole
        return pts_to_path(rect_pts(x, y, w, h))
    elif hole[0] == 'stadium':
        return stadium_path(hole[1], hole[2], hole[3], hole[4])
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


