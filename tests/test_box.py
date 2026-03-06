"""Tests for src/box.py — box panels + A-frame stand layout on 3mm ply sheet."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT as p, make_params
from src.geometry import bounding_box, bboxes_overlap

# Imported from box.py — will fail until box.py exists
from src.box import (
    layout, render, verify, generate, write,
    build_box_base, build_box_lid,
    build_box_long_wall, build_box_short_wall,
    build_stand_leg, build_stand_spreader,
)

EXPECTED_IDS = {
    "box_base", "box_lid",
    "box_long_wall_L", "box_long_wall_R",
    "box_short_wall_front", "box_short_wall_back",
    "stand_L", "stand_R",
    "stand_spreader",
}


# ---------------------------------------------------------------------------
# Part builder smoke tests
# ---------------------------------------------------------------------------

class TestPartBuilders:

    def test_box_base_dimensions(self):
        pts, holes = build_box_base(p)
        bb = bounding_box(pts)
        assert abs((bb[2] - bb[0]) - p["BOX_OUTER_L"]) < 0.1, \
            f"Base width: {bb[2]-bb[0]:.2f} != BOX_OUTER_L={p['BOX_OUTER_L']:.2f}"
        assert abs((bb[3] - bb[1]) - p["BOX_OUTER_W"]) < 0.1, \
            f"Base height: {bb[3]-bb[1]:.2f} != BOX_OUTER_W={p['BOX_OUTER_W']:.2f}"

    def test_box_base_no_holes(self):
        _, holes = build_box_base(p)
        assert holes == []

    def test_box_lid_fits_inside_box(self):
        """Lid interior dims must be <= box interior dims."""
        pts, _ = build_box_lid(p)
        bb = bounding_box(pts)
        lid_l = bb[2] - bb[0]
        lid_w = bb[3] - bb[1]
        assert lid_l <= p["BOX_INTERIOR_L"] + 1e-3, \
            f"Lid length {lid_l:.2f} exceeds BOX_INTERIOR_L={p['BOX_INTERIOR_L']:.2f}"
        assert lid_w <= p["BOX_INTERIOR_W"] + 1e-3, \
            f"Lid width {lid_w:.2f} exceeds BOX_INTERIOR_W={p['BOX_INTERIOR_W']:.2f}"

    def test_box_lid_no_holes(self):
        _, holes = build_box_lid(p)
        assert holes == []

    def test_box_long_wall_length(self):
        pts, _ = build_box_long_wall(p)
        bb = bounding_box(pts)
        long_dim = max(bb[2] - bb[0], bb[3] - bb[1])
        assert abs(long_dim - p["BOX_OUTER_L"]) < 0.1, \
            f"Long wall long dimension {long_dim:.2f} != BOX_OUTER_L={p['BOX_OUTER_L']:.2f}"

    def test_box_long_wall_height(self):
        """Long wall short dimension = BOX_INTERIOR_H + MAT3 (wall height + base tab protrusion)."""
        pts, _ = build_box_long_wall(p)
        bb = bounding_box(pts)
        short_dim = min(bb[2] - bb[0], bb[3] - bb[1])
        expected = p["BOX_INTERIOR_H"] + p["MAT3"]
        assert abs(short_dim - expected) < 0.1, \
            f"Long wall short dimension {short_dim:.2f} != BOX_INTERIOR_H+MAT3={expected:.2f}"

    def test_box_short_wall_length(self):
        """Short wall total width (including corner tabs) = BOX_OUTER_W."""
        pts, _ = build_box_short_wall(p)
        bb = bounding_box(pts)
        long_dim = max(bb[2] - bb[0], bb[3] - bb[1])
        assert abs(long_dim - p["BOX_OUTER_W"]) < 0.1, \
            f"Short wall long dim {long_dim:.2f} != BOX_OUTER_W={p['BOX_OUTER_W']:.2f}"

    def test_box_short_wall_height(self):
        """Short wall bbox height = BOX_INTERIOR_H + MAT3 - BOX_DADO_W (solid + base tab - lid slot)."""
        pts, _ = build_box_short_wall(p)
        bb = bounding_box(pts)
        short_dim = min(bb[2] - bb[0], bb[3] - bb[1])
        expected = p["BOX_INTERIOR_H"] + p["MAT3"] - p["BOX_DADO_W"]
        assert abs(short_dim - expected) < 0.1, \
            f"Short wall bbox height {short_dim:.2f} != BOX_INTERIOR_H+MAT3-BOX_DADO_W={expected:.2f}"

    def test_long_wall_has_corner_sockets(self):
        """Long wall has N=1 finger sockets at both ends (for short wall tabs).
        Portrait orientation: sockets open at y=0 and y=BOX_OUTER_L."""
        pts, _ = build_box_long_wall(p)
        ys = [pt[1] for pt in pts]
        # Socket back walls at y=MAT3 (top socket) and y=BOX_OUTER_L-MAT3 (bottom socket)
        assert any(abs(y - p["MAT3"]) < 1e-3 for y in ys), \
            f"No top socket back wall at y=MAT3={p['MAT3']:.1f}mm"
        assert any(abs(y - (p["BOX_OUTER_L"] - p["MAT3"])) < 1e-3 for y in ys), \
            f"No bottom socket back wall at y=BOX_OUTER_L-MAT3={p['BOX_OUTER_L']-p['MAT3']:.1f}mm"

    def test_short_wall_total_width_includes_tabs(self):
        """Short wall with corner tabs: total width = BOX_OUTER_W (not BOX_INTERIOR_W)."""
        pts, _ = build_box_short_wall(p)
        bb = bounding_box(pts)
        total_w = bb[2] - bb[0]
        assert abs(total_w - p["BOX_OUTER_W"]) < 0.1, \
            f"Short wall total width {total_w:.2f} != BOX_OUTER_W={p['BOX_OUTER_W']:.2f}"

    def test_short_wall_has_lid_slot_at_top(self):
        """Short wall bbox height = BOX_INTERIOR_H + MAT3 - BOX_DADO_W (full span minus open slot)."""
        pts, _ = build_box_short_wall(p)
        bb = bounding_box(pts)
        solid_h = bb[3] - bb[1]
        expected = p["BOX_INTERIOR_H"] + p["MAT3"] - p["BOX_DADO_W"]
        assert abs(solid_h - expected) < 0.1, \
            f"Short wall bbox height {solid_h:.2f} != expected {expected:.2f}"

    def test_long_wall_has_bottom_tabs(self):
        """Long wall portrait bbox width = BOX_INTERIOR_H + MAT3 (base tabs protrude)."""
        pts, _ = build_box_long_wall(p)
        bb = bounding_box(pts)
        short_dim = min(bb[2] - bb[0], bb[3] - bb[1])
        expected = p["BOX_INTERIOR_H"] + p["MAT3"]
        assert abs(short_dim - expected) < 0.1, \
            f"Long wall short dim {short_dim:.2f} != BOX_INTERIOR_H+MAT3={expected:.2f}"

    def test_long_wall_bottom_tab_count(self):
        """Long wall has BOX_BASE_NTABS_L bottom tabs: that many x-values at h+MAT3."""
        pts, _ = build_box_long_wall(p)
        tab_x = p["BOX_INTERIOR_H"] + p["MAT3"]
        count = sum(1 for pt in pts if abs(pt[0] - tab_x) < 1e-3)
        # Each tab contributes 2 points at x=h+MAT3 (the far corners of the tab)
        assert count == 2 * p["BOX_BASE_NTABS_L"], \
            f"Expected {2*p['BOX_BASE_NTABS_L']} pts at x={tab_x:.1f}, got {count}"

    def test_short_wall_has_bottom_tab(self):
        """Short wall has BOX_BASE_NTABS_S bottom tab: pts include y=BOX_INTERIOR_H+MAT3."""
        pts, _ = build_box_short_wall(p)
        tab_y = p["BOX_INTERIOR_H"] + p["MAT3"]
        count = sum(1 for pt in pts if abs(pt[1] - tab_y) < 1e-3)
        assert count == 2 * p["BOX_BASE_NTABS_S"], \
            f"Expected {2*p['BOX_BASE_NTABS_S']} pts at y={tab_y:.1f}, got {count}"

    def test_base_has_front_back_notches(self):
        """Base outline includes y=MAT3 (front notch) and y=BOX_OUTER_W-MAT3 (back notch)."""
        pts, _ = build_box_base(p)
        ys = [pt[1] for pt in pts]
        assert any(abs(y - p["MAT3"]) < 1e-3 for y in ys), \
            f"No front edge notch at y=MAT3={p['MAT3']:.1f}"
        assert any(abs(y - (p["BOX_OUTER_W"] - p["MAT3"])) < 1e-3 for y in ys), \
            f"No back edge notch at y=BOX_OUTER_W-MAT3={p['BOX_OUTER_W']-p['MAT3']:.1f}"

    def test_base_has_left_right_notches(self):
        """Base outline includes x=MAT3 (left notch) and x=BOX_OUTER_L-MAT3 (right notch)."""
        pts, _ = build_box_base(p)
        xs = [pt[0] for pt in pts]
        assert any(abs(x - p["MAT3"]) < 1e-3 for x in xs), \
            f"No left edge notch at x=MAT3={p['MAT3']:.1f}"
        assert any(abs(x - (p["BOX_OUTER_L"] - p["MAT3"])) < 1e-3 for x in xs), \
            f"No right edge notch at x=BOX_OUTER_L-MAT3={p['BOX_OUTER_L']-p['MAT3']:.1f}"

    def test_base_bbox_unchanged(self):
        """Base edge notches are concave — bbox remains BOX_OUTER_L × BOX_OUTER_W."""
        pts, _ = build_box_base(p)
        bb = bounding_box(pts)
        assert abs((bb[2] - bb[0]) - p["BOX_OUTER_L"]) < 0.1
        assert abs((bb[3] - bb[1]) - p["BOX_OUTER_W"]) < 0.1

    def test_stand_leg_dimensions(self):
        pts, _ = build_stand_leg(p)
        bb = bounding_box(pts)
        assert abs((bb[2] - bb[0]) - p["STAND_LEG_W"]) < 0.1
        assert abs((bb[3] - bb[1]) - p["STAND_LEG_L"]) < 0.1

    def test_stand_leg_has_mortise_hole(self):
        """Stand leg must have a rectangular mortise hole for the spreader tenon."""
        _, holes = build_stand_leg(p)
        assert len(holes) >= 1, "Stand leg needs at least 1 mortise hole for spreader tenon"
        rect_holes = [h for h in holes if h[0] == 'rect']
        assert len(rect_holes) >= 1, f"Need at least 1 rect hole; got holes: {holes}"

    def test_stand_leg_mortise_dimensions(self):
        """Mortise hole must match stand spreader mort dimensions."""
        _, holes = build_stand_leg(p)
        rect_holes = [h for h in holes if h[0] == 'rect']
        # Find a hole with the expected mortise dimensions
        mort_d = p["STAND_SPREAD_MORT_D"]   # = 15mm (depth/length of tenon)
        mort_w = p["STAND_SPREAD_MORT_W"]   # = 3.1mm (width of slot)
        found = False
        for h in rect_holes:
            _, x, y, w, h_dim = h
            if (abs(w - mort_d) < 0.2 and abs(h_dim - mort_w) < 0.2) or \
               (abs(h_dim - mort_d) < 0.2 and abs(w - mort_w) < 0.2):
                found = True
                break
        assert found, \
            f"No mortise hole matching {mort_d:.1f}×{mort_w:.1f}mm; holes={rect_holes}"

    def test_stand_R_mirrors_L(self):
        """Stand-R bounding box must be same size as Stand-L."""
        pts_l, _ = build_stand_leg(p)
        pts_r, _ = build_stand_leg(p)  # same function; layout mirrors it
        bb_l = bounding_box(pts_l)
        bb_r = bounding_box(pts_r)
        assert abs((bb_l[2] - bb_l[0]) - (bb_r[2] - bb_r[0])) < 1e-6
        assert abs((bb_l[3] - bb_l[1]) - (bb_r[3] - bb_r[1])) < 1e-6

    def test_stand_spreader_total_length(self):
        pts, _ = build_stand_spreader(p)
        bb = bounding_box(pts)
        total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]
        long_dim = max(bb[2] - bb[0], bb[3] - bb[1])
        assert abs(long_dim - total_l) < 0.1, \
            f"Spreader total length {long_dim:.2f} != {total_l:.2f}"

    def test_stand_spreader_width(self):
        pts, _ = build_stand_spreader(p)
        bb = bounding_box(pts)
        short_dim = min(bb[2] - bb[0], bb[3] - bb[1])
        assert abs(short_dim - p["STAND_SPREAD_W"]) < 0.1


# ---------------------------------------------------------------------------
# Layout tests — happy path
# ---------------------------------------------------------------------------

class TestLayout:

    def setup_method(self):
        self.placed = layout(p)
        self.by_id = {pt["id"]: pt for pt in self.placed}

    def test_part_count(self):
        assert len(self.placed) == len(EXPECTED_IDS), \
            f"Expected {len(EXPECTED_IDS)} parts, got {len(self.placed)}"

    def test_all_expected_ids_present(self):
        ids = {pt["id"] for pt in self.placed}
        assert ids == EXPECTED_IDS, \
            f"Missing: {EXPECTED_IDS - ids}; extra: {ids - EXPECTED_IDS}"

    def test_all_parts_within_sheet_bounds(self):
        M = p["MARGIN"]
        sw, sh = p["SHEET_W"], p["SHEET_H"]
        for part in self.placed:
            x0, y0, x1, y1 = part["bbox"]
            assert x0 >= M - 1e-6, f"{part['id']} left edge {x0:.3f} < margin {M}"
            assert y0 >= M - 1e-6, f"{part['id']} top edge {y0:.3f} < margin {M}"
            assert x1 <= sw - M + 1e-6, f"{part['id']} right {x1:.3f} > {sw-M}"
            assert y1 <= sh - M + 1e-6, f"{part['id']} bottom {y1:.3f} > {sh-M}"

    def test_no_part_overlaps(self):
        parts = self.placed
        for i, a in enumerate(parts):
            for j, b in enumerate(parts):
                if i >= j:
                    continue
                assert not bboxes_overlap(a["bbox"], b["bbox"]), \
                    f"'{a['id']}' and '{b['id']}' overlap: {a['bbox']} vs {b['bbox']}"

    def test_box_base_dimensions_on_sheet(self):
        bb = self.by_id["box_base"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["BOX_OUTER_L"]) < 0.1
        assert abs((bb[3] - bb[1]) - p["BOX_OUTER_W"]) < 0.1

    def test_stand_L_and_R_not_overlapping(self):
        sl = self.by_id["stand_L"]["bbox"]
        sr = self.by_id["stand_R"]["bbox"]
        assert not bboxes_overlap(sl, sr)

    def test_parts_have_bbox_key(self):
        for part in self.placed:
            x0, y0, x1, y1 = part["bbox"]
            assert x1 > x0
            assert y1 > y0


# ---------------------------------------------------------------------------
# Verify tests
# ---------------------------------------------------------------------------

class TestVerify:

    def setup_method(self):
        self.placed = layout(p)
        self.results = verify(self.placed, p)
        self.by_name = {n: (ok, d) for n, ok, d in self.results}

    def test_I1_passes(self):
        ok, detail = self.by_name["I-1"]
        assert ok, detail

    def test_I2_passes(self):
        ok, detail = self.by_name["I-2"]
        assert ok, detail

    def test_I12_passes(self):
        ok, detail = self.by_name["I-12"]
        assert ok, detail

    def test_no_failures(self):
        failures = [(n, d) for n, ok, d in self.results if not ok]
        assert not failures, f"Verify failures: {failures}"


# ---------------------------------------------------------------------------
# Generate / render tests
# ---------------------------------------------------------------------------

class TestGenerate:

    def setup_method(self):
        self.svg = generate(p)

    def test_returns_string(self):
        assert isinstance(self.svg, str)

    def test_contains_svg_tag(self):
        assert "<svg " in self.svg

    def test_ends_with_svg_close(self):
        assert self.svg.rstrip().endswith("</svg>")

    def test_contains_all_part_ids(self):
        for pid in EXPECTED_IDS:
            assert pid in self.svg, f"SVG missing part id '{pid}'"

    def test_all_paths_closed(self):
        import re
        d_values = re.findall(r' d="([^"]+)"', self.svg)
        assert d_values, "No path d-attributes found in SVG"
        for d in d_values:
            assert d.endswith("Z"), f"Unclosed path d: {d[:80]}"

    def test_fill_none(self):
        assert "fill:none" in self.svg or 'fill="none"' in self.svg


# ---------------------------------------------------------------------------
# Write tests
# ---------------------------------------------------------------------------

class TestWrite:

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_box.svg")
            result = write(p, path=path)
            assert result == path
            assert os.path.exists(path)

    def test_write_file_not_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_box.svg")
            write(p, path=path)
            assert os.path.getsize(path) > 500


# ---------------------------------------------------------------------------
# Unhappy-path tests
# ---------------------------------------------------------------------------

class TestUnhappyPath:

    def test_verify_detects_oob(self):
        placed = layout(p)
        for part in placed:
            if part["id"] == "box_base":
                x0, y0, x1, y1 = part["bbox"]
                part["bbox"] = (x0, y0, 700.0, y1)
                break
        results = verify(placed, p)
        by_name = {n: (ok, d) for n, ok, d in results}
        ok, detail = by_name["I-1"]
        assert not ok, f"I-1 should fail for OOB box_base; got: {detail}"

    def test_generate_250x350(self):
        alt = make_params(interior_w=250.0, interior_h=350.0)
        svg = generate(alt)
        assert "<svg " in svg
        assert svg.rstrip().endswith("</svg>")
