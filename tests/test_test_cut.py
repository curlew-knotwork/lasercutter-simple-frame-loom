"""Tests for src/test_cut.py — calibration / fit-test SVG generator."""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT as p, make_params
from src.geometry import bounding_box

from src.test_cut import (
    generate,
    layout,
    PIECE_IDS,
    TC_SHEET_W,
    TC_SHEET_H,
)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

class TestLayout:

    def setup_method(self):
        self.placed = layout(p)
        self.by_id = {pt["id"]: pt for pt in self.placed}

    def test_all_expected_pieces_present(self):
        ids = {pt["id"] for pt in self.placed}
        assert ids == set(PIECE_IDS), \
            f"Missing: {set(PIECE_IDS)-ids}; extra: {ids-set(PIECE_IDS)}"

    def test_all_within_sheet(self):
        M = p["MARGIN"]
        for part in self.placed:
            x0, y0, x1, y1 = part["bbox"]
            assert x0 >= M - 1e-6, f"{part['id']} left {x0:.2f} < margin"
            assert y0 >= M - 1e-6, f"{part['id']} top {y0:.2f} < margin"
            assert x1 <= TC_SHEET_W - M + 1e-6, f"{part['id']} right {x1:.2f} > {TC_SHEET_W-M}"
            assert y1 <= TC_SHEET_H - M + 1e-6, f"{part['id']} bottom {y1:.2f} > {TC_SHEET_H-M}"

    def test_no_overlaps(self):
        from src.geometry import bboxes_overlap
        parts = self.placed
        for i, a in enumerate(parts):
            for j, b in enumerate(parts):
                if i >= j:
                    continue
                assert not bboxes_overlap(a["bbox"], b["bbox"]), \
                    f"'{a['id']}' ∩ '{b['id']}': {a['bbox']} vs {b['bbox']}"


# ---------------------------------------------------------------------------
# Joint geometry — verify test pieces match box joint dimensions
# ---------------------------------------------------------------------------

class TestJointDimensions:

    def setup_method(self):
        self.placed = layout(p)
        self.by_id = {pt["id"]: pt for pt in self.placed}

    def test_corner_socket_depth(self):
        """tc_socket: corner socket back-wall at y=MAT3 (socket opens at y=0, 3mm deep)."""
        part = self.by_id["tc_socket"]
        ys = [pt[1] for pt in part["local_pts"]]
        assert any(abs(y - p["MAT3"]) < 1e-3 for y in ys), \
            f"No socket back wall at y=MAT3={p['MAT3']:.1f}; ys={sorted(set(ys))}"

    def test_corner_tab_protrusion(self):
        """tc_tab: tab extends to x=-MAT3 (3mm protrusion)."""
        part = self.by_id["tc_tab"]
        xs = [pt[0] for pt in part["local_pts"]]
        assert any(abs(x - (-p["MAT3"])) < 1e-3 for x in xs), \
            f"No tab tip at x=-MAT3={-p['MAT3']:.1f}; xs={sorted(set(xs))}"

    def test_base_notch_depth(self):
        """tc_base_notch: notch depth at x=MAT3 (notch opens at x=0, goes 3mm inward)."""
        part = self.by_id["tc_base_notch"]
        xs = [pt[0] for pt in part["local_pts"]]
        assert any(abs(x - p["MAT3"]) < 1e-3 for x in xs), \
            f"No notch depth at x=MAT3={p['MAT3']:.1f}; xs={sorted(set(xs))}"

    def test_lid_slot_depth(self):
        """tc_lid_slot: top slot depth = BOX_DADO_W."""
        part = self.by_id["tc_lid_slot"]
        ys = [pt[1] for pt in part["local_pts"]]
        assert any(abs(y - p["BOX_DADO_W"]) < 1e-3 for y in ys), \
            f"No lid slot back wall at y=BOX_DADO_W={p['BOX_DADO_W']:.2f}; ys={sorted(set(ys))}"

    def test_tab_width_matches_socket_width(self):
        """Corner tab width == BOX_TAB_W (matches long-wall socket width)."""
        part = self.by_id["tc_tab"]
        xs = [pt[0] for pt in part["local_pts"]]
        # Tab spans from x=-MAT3 to x=0; tab height = BOX_TAB_W
        tab_pts = [pt for pt in part["local_pts"] if abs(pt[0] - (-p["MAT3"])) < 1e-3]
        ys_at_tip = [pt[1] for pt in tab_pts]
        if len(ys_at_tip) >= 2:
            tw = max(ys_at_tip) - min(ys_at_tip)
            assert abs(tw - p["BOX_TAB_W"]) < 0.1, \
                f"Tab width {tw:.2f} != BOX_TAB_W={p['BOX_TAB_W']:.2f}"


# ---------------------------------------------------------------------------
# SVG generation
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

    def test_all_paths_closed(self):
        d_values = re.findall(r' d="([^"]+)"', self.svg)
        assert d_values, "No path d-attributes found"
        for d in d_values:
            assert d.endswith("Z"), f"Unclosed path: {d[:80]}"

    def test_piece_ids_in_svg(self):
        for pid in PIECE_IDS:
            assert pid in self.svg, f"SVG missing piece id '{pid}'"

    def test_generate_250x350(self):
        alt = make_params(interior_w=250.0, interior_h=350.0)
        svg = generate(alt)
        assert "<svg " in svg
        assert svg.rstrip().endswith("</svg>")
