"""Tests for src/geometry.py — path builders and geometric primitives."""

import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.geometry import (
    translate, mirror_x, bounding_box, pts_to_path,
    circle_path, ellipse_path, rect_pts, bboxes_overlap,
    rail_pts, stile_pts, crossbar_pts, beater_pts,
    rect_hole, translate_hole, hole_to_path,
    stadium_path, stadium_hole,
    rail_path, beater_path,
)
from src.params import DEFAULT as p


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def test_rect_pts_clockwise():
    pts = rect_pts(0, 0, 10, 5)
    assert pts == [(0,0),(10,0),(10,5),(0,5)]

def test_translate():
    pts = [(0,0),(1,0),(1,1)]
    result = translate(pts, 5, 3)
    assert result == [(5,3),(6,3),(6,4)]

def test_mirror_x():
    pts = [(0,0),(2,0),(2,1)]
    result = mirror_x(pts, 1.0)
    assert abs(result[0][0] - 2.0) < 1e-9
    assert abs(result[1][0] - 0.0) < 1e-9

def test_bounding_box():
    pts = [(1,2),(5,0),(3,4)]
    assert bounding_box(pts) == (1, 0, 5, 4)

def test_pts_to_path_closes():
    pts = [(0,0),(10,0),(10,10)]
    path = pts_to_path(pts)
    assert path.endswith("Z")
    assert path.startswith("M ")

def test_bboxes_overlap_true():
    assert bboxes_overlap((0,0,10,10),(5,5,15,15))

def test_bboxes_overlap_false_adjacent():
    # Touching edges do not overlap (open interval check)
    assert not bboxes_overlap((0,0,10,10),(10,0,20,10))

def test_bboxes_overlap_false_separated():
    assert not bboxes_overlap((0,0,5,5),(10,10,15,15))

def test_circle_path_closed():
    path = circle_path(10, 10, 5)
    assert "Z" in path

def test_ellipse_path_closed():
    path = ellipse_path(10, 10, 8, 3)
    assert "Z" in path


# ---------------------------------------------------------------------------
# rail_pts
# ---------------------------------------------------------------------------

class TestRailPts:

    def setup_method(self):
        self.notch_cxs = [p["NOTCH_START_X"] + i * p["NOTCH_PITCH"]
                          for i in range(p["NOTCH_COUNT"])]
        self.pts = rail_pts(
            p["FRAME_OUTER_W"], p["RAIL_W"],
            p["SOCK_W"], p["TAB_L"],
            self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"],
            notches_open_down=True,
        )
        self.bb = bounding_box(self.pts)

    def test_rail_x_span(self):
        """Rail spans 0 to FRAME_OUTER_W in x."""
        xmin, _, xmax, _ = self.bb
        assert abs(xmin) < 1e-6
        assert abs(xmax - p["FRAME_OUTER_W"]) < 1e-6

    def test_rail_y_top(self):
        """Top of rail at y=0."""
        assert abs(self.bb[1]) < 1e-6

    def test_rail_y_bottom_includes_notch_depth(self):
        """Bottom of top rail bounding box = RAIL_W + NOTCH_D (notches extend down)."""
        expected = p["RAIL_W"] + p["NOTCH_D"]
        assert abs(self.bb[3] - expected) < 1e-6

    def test_socket_does_not_protrude_outside_rail(self):
        """Socket is concave — no x < 0 or x > FRAME_OUTER_W."""
        xs = [pt[0] for pt in self.pts]
        assert min(xs) >= 0.0 - 1e-9
        assert max(xs) <= p["FRAME_OUTER_W"] + 1e-9

    def test_socket_depth_correct(self):
        """Socket back wall at x = FRAME_OUTER_W - TAB_L and x = TAB_L."""
        xs = sorted(set(round(pt[0], 4) for pt in self.pts))
        # Right socket back wall
        right_back = p["FRAME_OUTER_W"] - p["TAB_L"]
        assert any(abs(x - right_back) < 1e-3 for x in xs), \
            f"No point at right socket back wall x={right_back:.4f}: {xs[:10]}"
        # Left socket back wall
        left_back = p["TAB_L"]
        assert any(abs(x - left_back) < 1e-3 for x in xs), \
            f"No point at left socket back wall x={left_back:.4f}: {xs[:10]}"

    def test_notch_count(self):
        """31 notches → 31 downward tips (y = RAIL_W + NOTCH_D)."""
        notch_y = p["RAIL_W"] + p["NOTCH_D"]
        notch_tips = [pt for pt in self.pts if abs(pt[1] - notch_y) < 1e-6]
        # Each notch has 2 bottom corners
        assert len(notch_tips) == 2 * p["NOTCH_COUNT"], \
            f"Expected {2*p['NOTCH_COUNT']} notch tips, got {len(notch_tips)}"

    def test_bottom_rail_notches_open_up(self):
        """Bottom rail notches open upward (y < 0 = above outer edge)."""
        pts_up = rail_pts(
            p["FRAME_OUTER_W"], p["RAIL_W"],
            p["SOCK_W"], p["TAB_L"],
            self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"],
            notches_open_down=False,
        )
        bb = bounding_box(pts_up)
        # Top of bounding box should be at y = -(NOTCH_D) (notches go up)
        assert abs(bb[1] - (-p["NOTCH_D"])) < 1e-6, \
            f"Bottom rail ymin should be -{p['NOTCH_D']}, got {bb[1]}"
        # Bottom of bounding box at y = RAIL_W
        assert abs(bb[3] - p["RAIL_W"]) < 1e-6


# ---------------------------------------------------------------------------
# stile_pts
# ---------------------------------------------------------------------------

class TestStilePts:

    def setup_method(self):
        # D-13: stile_pts takes no mortises; clean outline only
        self.pts = stile_pts(
            p["STILE_W"], p["STILE_BODY_H"],
            p["TAB_W"], p["TAB_L"],
        )
        self.bb = bounding_box(self.pts)

    def test_stile_x_span(self):
        """Stile spans 0 to STILE_W in x (clean outline, no protrusion)."""
        xmin, _, xmax, _ = self.bb
        assert abs(xmin) < 1e-6
        assert abs(xmax - p["STILE_W"]) < 1e-6

    def test_stile_tab_protrusion_top(self):
        """Top tab protrudes to y = -TAB_L."""
        assert abs(self.bb[1] - (-p["TAB_L"])) < 1e-6

    def test_stile_tab_protrusion_bottom(self):
        """Bottom tab protrudes to y = STILE_BODY_H + TAB_L."""
        expected = p["STILE_BODY_H"] + p["TAB_L"]
        assert abs(self.bb[3] - expected) < 1e-6

    def test_stile_outline_is_clean(self):
        """D-13: no concave mortise indentations — all x ∈ {0, STILE_W, tab_x0, tab_x1}."""
        tab_x0 = (p["STILE_W"] - p["TAB_W"]) / 2.0
        tab_x1 = tab_x0 + p["TAB_W"]
        valid_xs = {0.0, p["STILE_W"], tab_x0, tab_x1}
        for x, y in self.pts:
            assert any(abs(x - vx) < 1e-3 for vx in valid_xs), \
                f"Unexpected x={x:.4f} in stile outline"

    def test_stile_has_12_points(self):
        """Clean stile outline: 12 points (4 for body corners + 8 for two tabs)."""
        assert len(self.pts) == 12, f"Expected 12 stile points, got {len(self.pts)}"

    def test_tab_width(self):
        """Tab spans from TAB_X0 to TAB_X0 + TAB_W."""
        tab_x0 = (p["STILE_W"] - p["TAB_W"]) / 2.0
        tab_x1 = tab_x0 + p["TAB_W"]
        xs = [pt[0] for pt in self.pts]
        assert any(abs(x - tab_x0) < 1e-4 for x in xs)
        assert any(abs(x - tab_x1) < 1e-4 for x in xs)

    def test_mirrored_stile_R(self):
        """Right stile is left stile mirrored about x = STILE_W/2."""
        pts_r = mirror_x(self.pts, p["STILE_W"] / 2.0)
        bb_r = bounding_box(pts_r)
        assert abs(bb_r[2] - p["STILE_W"]) < 1e-6
        assert abs(bb_r[0]) < 1e-6


# ---------------------------------------------------------------------------
# crossbar_pts
# ---------------------------------------------------------------------------

class TestCrossbarPts:

    def setup_method(self):
        self.pts = crossbar_pts(p["CROSS_BODY_W"], p["CROSS_H"])

    def test_total_length(self):
        """D-13: CROSS_TOTAL_L == CROSS_BODY_W == INTERIOR_W (no tenons)."""
        bb = bounding_box(self.pts)
        assert abs(bb[2] - p["CROSS_TOTAL_L"]) < 1e-6

    def test_height(self):
        bb = bounding_box(self.pts)
        assert abs(bb[3] - p["CROSS_H"]) < 1e-6

    def test_is_rectangle(self):
        """D-13: crossbar is a plain rectangle (4 points)."""
        assert len(self.pts) == 4


# ---------------------------------------------------------------------------
# beater_pts
# ---------------------------------------------------------------------------

class TestBeaterPts:

    def setup_method(self):
        self.pts = beater_pts(
            p["BEATER_W"], p["BEATER_HANDLE_H"],
            p["BEATER_TOOTH_H"], p["BEATER_TOOTH_W"],
            p["BEATER_TOOTH_PITCH"], p["BEATER_TOOTH_COUNT"],
        )

    def test_beater_x_span(self):
        bb = bounding_box(self.pts)
        assert abs(bb[0]) < 1e-6
        assert abs(bb[2] - p["BEATER_W"]) < 1e-6

    def test_beater_total_height(self):
        bb = bounding_box(self.pts)
        expected = p["BEATER_HANDLE_H"] + p["BEATER_TOOTH_H"]
        assert abs(bb[3] - expected) < 1e-6

    def test_tooth_count_points(self):
        """Each tooth contributes 4 points (right-wall-down, bottom, left-wall-up, gap)."""
        # BEATER_TOOTH_COUNT teeth
        tooth_tips = [pt for pt in self.pts
                      if abs(pt[1] - (p["BEATER_HANDLE_H"] + p["BEATER_TOOTH_H"])) < 1e-6]
        assert len(tooth_tips) == 2 * p["BEATER_TOOTH_COUNT"], \
            f"Expected {2*p['BEATER_TOOTH_COUNT']} tooth tips, got {len(tooth_tips)}"


# ---------------------------------------------------------------------------
# rect_hole / translate_hole / hole_to_path
# ---------------------------------------------------------------------------

class TestRectHole:

    def test_rect_hole_tuple_kind(self):
        h = rect_hole(10, 20, 5, 3)
        assert h[0] == 'rect'

    def test_rect_hole_to_path_closed(self):
        h = rect_hole(10, 20, 5, 3)
        path = hole_to_path(h)
        assert path.endswith("Z")

    def test_rect_hole_to_path_starts_at_corner(self):
        h = rect_hole(10, 20, 5, 3)
        path = hole_to_path(h)
        # First point must be at (10, 20)
        assert "10.0000,20.0000" in path

    def test_rect_hole_translate(self):
        h = rect_hole(10, 20, 5, 3)
        h2 = translate_hole(h, 3, 7)
        assert h2[0] == 'rect'
        path = hole_to_path(h2)
        assert "13.0000,27.0000" in path

    def test_rect_hole_dimensions_preserved_on_translate(self):
        h = rect_hole(0, 0, 15, 3.1)
        h2 = translate_hole(h, 100, 200)
        # Width (15) and height (3.1) unchanged
        assert abs(h2[3] - 15.0) < 1e-9
        assert abs(h2[4] - 3.1) < 1e-9


# ---------------------------------------------------------------------------
# stadium_path / stadium_hole
# cx=10, cy=10, r=1.5, h=8  →  h_rect=5, top_cy=7.5, bot_cy=12.5
# ---------------------------------------------------------------------------

class TestStadiumPath:

    def test_stadium_path_closed(self):
        path = stadium_path(10, 10, 1.5, 8.0)
        assert path.rstrip().endswith("Z")

    def test_stadium_path_starts_with_M(self):
        path = stadium_path(10, 10, 1.5, 8.0)
        assert path.startswith("M ")

    def test_stadium_path_has_two_arcs(self):
        path = stadium_path(10, 10, 1.5, 8.0)
        assert path.count(" A ") == 2

    def test_stadium_path_arc_sweep_flags(self):
        """Both caps use sweep=0: top goes above top_cy, bottom goes below bot_cy."""
        path = stadium_path(10, 10, 1.5, 8.0)
        # Both arcs must use sweep=0 (CCW, outward for both caps)
        assert path.count("0 1,0") == 2, \
            f"Expected 2 occurrences of sweep=0 arc, got: {path}"

    def test_stadium_path_has_line_segment(self):
        path = stadium_path(10, 10, 1.5, 8.0)
        assert " L " in path

    def test_stadium_path_start_point(self):
        """Start at (cx+r, top_cy) = (11.5, 7.5)."""
        path = stadium_path(10, 10, 1.5, 8.0)
        assert "11.5000,7.5000" in path

    def test_stadium_path_left_edge(self):
        """Left edge of arcs at cx-r = 8.5."""
        path = stadium_path(10, 10, 1.5, 8.0)
        assert "8.5000" in path

    def test_stadium_path_top_cap_y(self):
        """Top semicircle center at top_cy=7.5; arc endpoints at x=±r, y=7.5."""
        path = stadium_path(10, 10, 1.5, 8.0)
        # Both arc endpoints on top cap share y=7.5
        assert "7.5000" in path

    def test_stadium_path_bottom_cap_y(self):
        """Bottom semicircle center at bot_cy=12.5; arc endpoints at y=12.5."""
        path = stadium_path(10, 10, 1.5, 8.0)
        assert "12.5000" in path

    def test_stadium_hole_tuple_type(self):
        h = stadium_hole(10, 10, 1.5, 8.0)
        assert h[0] == 'stadium'

    def test_stadium_hole_params(self):
        h = stadium_hole(10, 10, 1.5, 8.0)
        assert h[1] == 10   # cx
        assert h[2] == 10   # cy
        assert h[3] == 1.5  # r
        assert h[4] == 8.0  # h

    def test_stadium_hole_to_path_closed(self):
        h = stadium_hole(10, 10, 1.5, 8.0)
        path = hole_to_path(h)
        assert path.rstrip().endswith("Z")

    def test_stadium_hole_translate_shifts_cx_cy(self):
        h = stadium_hole(10, 10, 1.5, 8.0)
        h2 = translate_hole(h, 5, 3)
        assert h2[0] == 'stadium'
        assert abs(h2[1] - 15.0) < 1e-9   # cx shifted
        assert abs(h2[2] - 13.0) < 1e-9   # cy shifted
        assert abs(h2[3] - 1.5) < 1e-9    # r unchanged
        assert abs(h2[4] - 8.0) < 1e-9    # h unchanged


# ---------------------------------------------------------------------------
# rail_path / beater_path — rounded corner path builders (D-25)
# ---------------------------------------------------------------------------

class TestRailPath:

    def setup_method(self):
        self.notch_cxs = [p["NOTCH_START_X"] + i * p["NOTCH_PITCH"]
                          for i in range(p["NOTCH_COUNT"])]

    def test_rail_path_returns_string(self):
        s = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                      self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.5)
        assert isinstance(s, str)

    def test_rail_path_closed(self):
        s = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                      self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.5)
        assert s.rstrip().endswith("Z")

    def test_rail_path_has_arcs_when_corner_r_nonzero(self):
        s = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                      self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.5)
        assert " A " in s

    def test_rail_path_no_arcs_when_corner_r_zero(self):
        s = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                      self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.0)
        assert " A " not in s

    def test_rail_path_arc_count(self):
        s = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                      self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.5)
        arc_count = s.count(" A ")
        assert arc_count == 4 * p["NOTCH_COUNT"], \
            f"Expected {4*p['NOTCH_COUNT']} arcs, got {arc_count}"

    def test_rail_path_notch_arc_sweep_order(self):
        """Single notch: arc sweep order must be [0,1,1,0] — outer concave, inner convex. P-C7."""
        import re
        # One notch at cx=50, rail 100 wide × 27 tall, notch_d=5, corner_r=0.5
        s = rail_path(100.0, 27.0, 7.0, 6.0, [50.0], 2.0, 5.0, corner_r=0.5)
        sweeps = [int(m) for m in re.findall(r"0 0,(\d)", s)]
        # 4 notch arcs; outer two are concave (sweep=0), inner two are convex (sweep=1)
        assert sweeps == [0, 1, 1, 0], \
            f"Expected arc sweep order [0,1,1,0], got {sweeps}"

    def test_rail_path_offset_shifts_start(self):
        import re
        s0 = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                       self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.5)
        s1 = rail_path(p["FRAME_OUTER_W"], p["RAIL_W"], p["SOCK_W"], p["TAB_L"],
                       self.notch_cxs, p["NOTCH_W"], p["NOTCH_D"], corner_r=0.5,
                       ox=10.0, oy=20.0)
        m0 = re.search(r"M ([\d.\-]+),([\d.\-]+)", s0)
        m1 = re.search(r"M ([\d.\-]+),([\d.\-]+)", s1)
        assert m0 and m1
        assert abs(float(m1.group(1)) - float(m0.group(1)) - 10.0) < 1e-3
        assert abs(float(m1.group(2)) - float(m0.group(2)) - 20.0) < 1e-3


class TestBeaterPath:

    def test_beater_path_returns_string(self):
        s = beater_path(p["BEATER_W"], p["BEATER_HANDLE_H"], p["BEATER_TOOTH_H"],
                        p["BEATER_TOOTH_W"], p["BEATER_TOOTH_PITCH"],
                        p["BEATER_TOOTH_COUNT"], corner_r=0.5)
        assert isinstance(s, str)

    def test_beater_path_closed(self):
        s = beater_path(p["BEATER_W"], p["BEATER_HANDLE_H"], p["BEATER_TOOTH_H"],
                        p["BEATER_TOOTH_W"], p["BEATER_TOOTH_PITCH"],
                        p["BEATER_TOOTH_COUNT"], corner_r=0.5)
        assert s.rstrip().endswith("Z")

    def test_beater_path_has_arcs(self):
        s = beater_path(p["BEATER_W"], p["BEATER_HANDLE_H"], p["BEATER_TOOTH_H"],
                        p["BEATER_TOOTH_W"], p["BEATER_TOOTH_PITCH"],
                        p["BEATER_TOOTH_COUNT"], corner_r=0.5)
        assert " A " in s

    def test_beater_path_arc_count(self):
        s = beater_path(p["BEATER_W"], p["BEATER_HANDLE_H"], p["BEATER_TOOTH_H"],
                        p["BEATER_TOOTH_W"], p["BEATER_TOOTH_PITCH"],
                        p["BEATER_TOOTH_COUNT"], corner_r=0.5)
        arc_count = s.count(" A ")
        assert arc_count == 4 * p["BEATER_TOOTH_COUNT"] + 4, \
            f"Expected {4*p['BEATER_TOOTH_COUNT']+4} arcs, got {arc_count}"

class TestRoundedPtsToPath:

    def test_rounded_pts_closed(self):
        from src.geometry import rounded_pts_to_path
        pts = [(0,0),(10,0),(10,10),(0,10)]
        s = rounded_pts_to_path(pts, 0.5)
        assert s.rstrip().endswith("Z")

    def test_rounded_pts_arc_count_equals_corner_count(self):
        from src.geometry import rounded_pts_to_path
        pts = [(0,0),(10,0),(10,10),(0,10)]
        s = rounded_pts_to_path(pts, 0.5)
        assert s.count(" A ") == 4

    def test_rounded_pts_zero_r_no_arcs(self):
        from src.geometry import rounded_pts_to_path
        pts = [(0,0),(10,0),(10,10),(0,10)]
        s = rounded_pts_to_path(pts, 0.0)
        assert " A " not in s

    def test_convex_corners_sweep_outward(self):
        """Convex corners (CW rect) must use sweep=1 — outward arc, not a cookie bite."""
        from src.geometry import rounded_pts_to_path
        pts = [(0,0),(10,0),(10,10),(0,10)]  # CW rect, all convex corners
        s = rounded_pts_to_path(pts, 1.0)
        # sweep=1 produces outward (convex) fillet; sweep=0 cuts a concave bite
        # SVG arc format: A rx,ry x-rot large-arc,sweep ex,ey
        # sweep=1 → "0,1"; sweep=0 → "0,0"
        assert "0,1 " in s,  "Expected sweep=1 for convex corners"
        assert "0,0 " not in s, "sweep=0 found — concave bite bug"

    def test_shuttle_path_returns_string(self):
        from src.geometry import shuttle_path
        s = shuttle_path(p["SHUTTLE_L"], p["SHUTTLE_W"],
                         p["SHUTTLE_TAPER_L"], p["SHUTTLE_NOTCH_HW"],
                         corner_r=0.5)
        assert isinstance(s, str)

    def test_shuttle_path_closed(self):
        from src.geometry import shuttle_path
        s = shuttle_path(p["SHUTTLE_L"], p["SHUTTLE_W"],
                         p["SHUTTLE_TAPER_L"], p["SHUTTLE_NOTCH_HW"],
                         corner_r=0.5)
        assert s.rstrip().endswith("Z")

    def test_shuttle_path_arc_count(self):
        """10 corners, but body/taper junctions (4) have r=0 (D-28 cookie-bite fix) → 6 arcs."""
        from src.geometry import shuttle_path
        s = shuttle_path(p["SHUTTLE_L"], p["SHUTTLE_W"],
                         p["SHUTTLE_TAPER_L"], p["SHUTTLE_NOTCH_HW"],
                         corner_r=0.5)
        assert s.count(" A ") == 6, \
            f"Expected 6 arcs (4 body/taper corners at r=0), got {s.count(' A ')}"
