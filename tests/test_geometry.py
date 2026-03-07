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
    triangle_pts,
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
# triangle_pts (D-18 — solid right-triangle stand side piece)
# ---------------------------------------------------------------------------

class TestTrianglePts:

    def setup_method(self):
        # Use D-18 stand params
        upright_notch_ys = [
            p["STAND_MORT_Y_TOP"], p["STAND_MORT_Y_MID"], p["STAND_MORT_Y_BOT"]
        ]
        base_notch_xs = [p["STAND_BASE_NOTCH_X1"], p["STAND_BASE_NOTCH_X2"]]
        self.pts = triangle_pts(
            p["STAND_UPRIGHT_H"], p["STAND_BASE_L"],
            upright_notch_ys, base_notch_xs,
            p["STAND_NOTCH_W"], p["STAND_NOTCH_D"],
        )
        self.bb = bounding_box(self.pts)

    def test_bbox_width(self):
        """Bounding box width = STAND_BASE_L = 240mm."""
        assert abs((self.bb[2] - self.bb[0]) - p["STAND_BASE_L"]) < 1e-6

    def test_bbox_height(self):
        """Bounding box height = STAND_UPRIGHT_H = 420mm."""
        assert abs((self.bb[3] - self.bb[1]) - p["STAND_UPRIGHT_H"]) < 1e-6

    def test_top_back_corner(self):
        """Origin point (0, 0) present in polygon."""
        assert any(abs(pt[0]) < 1e-9 and abs(pt[1]) < 1e-9 for pt in self.pts), \
            "Origin (0,0) not in polygon"

    def test_bottom_front_corner(self):
        """Bottom-front corner (STAND_BASE_L, STAND_UPRIGHT_H) present."""
        bl = p["STAND_BASE_L"]
        uh = p["STAND_UPRIGHT_H"]
        assert any(abs(pt[0] - bl) < 1e-9 and abs(pt[1] - uh) < 1e-9
                   for pt in self.pts), "Bottom-front corner not found"

    def test_upright_notches_concave(self):
        """Upright (left) notches go INTO body: no x < 0."""
        xs = [pt[0] for pt in self.pts]
        assert min(xs) >= -1e-9

    def test_base_notches_concave(self):
        """Base (bottom) notches go INTO body: no y > STAND_UPRIGHT_H."""
        ys = [pt[1] for pt in self.pts]
        assert max(ys) <= p["STAND_UPRIGHT_H"] + 1e-9

    def test_upright_notch_depth(self):
        """Upright notches reach STAND_NOTCH_D from left edge."""
        nd = p["STAND_NOTCH_D"]
        pts_at_depth = [pt for pt in self.pts if abs(pt[0] - nd) < 1e-6]
        # 3 notches × 2 points at depth = 6
        assert len(pts_at_depth) >= 6, \
            f"Expected ≥6 pts at upright notch depth x={nd}, got {len(pts_at_depth)}"

    def test_base_notch_depth(self):
        """Base notches reach STAND_NOTCH_D up from bottom."""
        nd = p["STAND_NOTCH_D"]
        uh = p["STAND_UPRIGHT_H"]
        pts_at_depth = [pt for pt in self.pts if abs(pt[1] - (uh - nd)) < 1e-6]
        # 2 notches × 2 points at depth = 4
        assert len(pts_at_depth) >= 4, \
            f"Expected ≥4 pts at base notch depth y={uh-nd:.2f}, got {len(pts_at_depth)}"

    def test_upright_notch_y_positions(self):
        """All three upright notch centres appear as edge points."""
        nw = p["STAND_NOTCH_W"]
        nd = p["STAND_NOTCH_D"]
        for cy in [p["STAND_MORT_Y_TOP"], p["STAND_MORT_Y_MID"], p["STAND_MORT_Y_BOT"]]:
            # Expect pts at (0, cy-nw/2) and (0, cy+nw/2) on the left edge
            y0_ok = any(abs(pt[0]) < 1e-9 and abs(pt[1] - (cy - nw/2)) < 0.01
                        for pt in self.pts)
            y1_ok = any(abs(pt[0]) < 1e-9 and abs(pt[1] - (cy + nw/2)) < 0.01
                        for pt in self.pts)
            assert y0_ok and y1_ok, \
                f"Notch edge pts missing at y-centre {cy}: y0={cy-nw/2}, y1={cy+nw/2}"

    def test_base_notch_x_positions(self):
        """Both base notch centres appear as edge points."""
        nw = p["STAND_NOTCH_W"]
        uh = p["STAND_UPRIGHT_H"]
        for cx in [p["STAND_BASE_NOTCH_X1"], p["STAND_BASE_NOTCH_X2"]]:
            x0_ok = any(abs(pt[1] - uh) < 1e-9 and abs(pt[0] - (cx - nw/2)) < 0.01
                        for pt in self.pts)
            x1_ok = any(abs(pt[1] - uh) < 1e-9 and abs(pt[0] - (cx + nw/2)) < 0.01
                        for pt in self.pts)
            assert x0_ok and x1_ok, \
                f"Base notch edge pts missing at x-centre {cx}: x0={cx-nw/2}, x1={cx+nw/2}"

    def test_no_plain_rectangle(self):
        """Triangle with 5 notches has >3 polygon vertices."""
        assert len(self.pts) > 3, f"Expected >3 pts, got {len(self.pts)}"
