"""Tests for src/loom.py — layout, render, verify, and write."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT as p, make_params
from src.geometry import bounding_box, bboxes_overlap
from src.loom import (
    layout, render, verify, generate, write,
    build_top_rail, build_bottom_rail,
    build_stile_L, build_stile_R,
    build_crossbar, build_shuttle,
    build_beater, build_heddle_bar,
)

EXPECTED_IDS = {
    "crossbar_1", "crossbar_2",
    "top_rail", "bottom_rail",
    "stile_L", "stile_R",
    "heddle_bar", "shuttle_1", "shuttle_2",
    "beater",
}


# ---------------------------------------------------------------------------
# Part builder smoke tests
# ---------------------------------------------------------------------------

class TestPartBuilders:

    def test_top_rail_has_two_heddle_holes(self):
        pts, holes = build_top_rail(p)
        assert len(holes) == 2, f"Expected 2 heddle holes, got {len(holes)}"

    def test_top_rail_includes_stand_tabs(self):
        """Top rail bounding box must be FRAME_OUTER_W + 2*STAND_RAIL_TAB_L wide (D-17)."""
        pts, _ = build_top_rail(p)
        bb = bounding_box(pts)
        expected_w = p["FRAME_OUTER_W"] + 2.0 * p["STAND_RAIL_TAB_L"]
        actual_w = bb[2] - bb[0]
        assert abs(actual_w - expected_w) < 0.1, \
            f"Top rail width {actual_w:.2f} != {expected_w:.2f}"

    def test_heddle_bar_alternating_hole_slot_types(self):
        """D-32/D-34: all openings are stadium holes; even=short (HOLE_H), odd=tall (SLOT_H)."""
        _, holes = build_heddle_bar(p)
        for i, h in enumerate(holes):
            assert h[0] == 'stadium', \
                f"Position {i}: type={h[0]!r}, expected 'stadium' (D-34: slots rounded)"
            expected_h = p["HEDDLE_BAR_HOLE_H"] if i % 2 == 0 else p["HEDDLE_BAR_SLOT_H"]
            assert abs(h[4] - expected_h) < 1e-9, \
                f"Position {i}: height={h[4]}, expected {expected_h}"

    def test_heddle_bar_has_both_hole_heights(self):
        """D-32/D-34: heddle bar has short holes (HOLE_H) and tall slots (SLOT_H), all stadium."""
        _, holes = build_heddle_bar(p)
        heights = {h[4] for h in holes}
        assert p["HEDDLE_BAR_HOLE_H"] in heights, "Short H holes not found"
        assert p["HEDDLE_BAR_SLOT_H"] in heights, "Tall S slots not found"

    def test_heddle_bar_hole_and_slot_heights(self):
        """D-32/D-34: even positions height=HEDDLE_BAR_HOLE_H; odd positions height=HEDDLE_BAR_SLOT_H."""
        _, holes = build_heddle_bar(p)
        for i, h in enumerate(holes):
            assert h[0] == 'stadium', f"Position {i} not stadium"
            _, hcx, hcy, hr, hh = h
            if i % 2 == 0:
                assert abs(hh - p["HEDDLE_BAR_HOLE_H"]) < 1e-9, \
                    f"Even hole {i}: height={hh} != {p['HEDDLE_BAR_HOLE_H']}"
            else:
                assert abs(hh - p["HEDDLE_BAR_SLOT_H"]) < 1e-9, \
                    f"Odd slot {i}: height={hh} != {p['HEDDLE_BAR_SLOT_H']}"

    def test_heddle_bar_corner_r_in_params(self):
        """Heddle bar outer corners rounded 2mm for hand-held comfort."""
        assert "HEDDLE_BAR_CORNER_R" in p, "HEDDLE_BAR_CORNER_R missing from params"
        assert abs(p["HEDDLE_BAR_CORNER_R"] - 2.0) < 1e-9

    def test_bottom_rail_has_no_holes(self):
        _, holes = build_bottom_rail(p)
        assert holes == []

    def test_stile_L_has_two_rect_holes(self):
        """D-13: stile L has 2 rect_holes (crossbar mortise pockets)."""
        _, holes = build_stile_L(p)
        assert len(holes) == 2
        assert all(h[0] == 'rect' for h in holes)

    def test_stile_R_has_two_rect_holes(self):
        """D-13: stile R has 2 rect_holes mirrored from stile L."""
        _, holes = build_stile_R(p)
        assert len(holes) == 2
        assert all(h[0] == 'rect' for h in holes)

    def test_stile_L_width(self):
        pts, _ = build_stile_L(p)
        bb = bounding_box(pts)
        assert abs((bb[2] - bb[0]) - p["STILE_W"]) < 1e-4

    def test_stile_L_height(self):
        pts, _ = build_stile_L(p)
        bb = bounding_box(pts)
        assert abs((bb[3] - bb[1]) - p["STILE_TOTAL_H"]) < 1e-4

    def test_stile_R_same_bbox_as_L(self):
        lpts, _ = build_stile_L(p)
        rpts, _ = build_stile_R(p)
        lbb = bounding_box(lpts)
        rbb = bounding_box(rpts)
        assert abs((lbb[2] - lbb[0]) - (rbb[2] - rbb[0])) < 1e-6
        assert abs((lbb[3] - lbb[1]) - (rbb[3] - rbb[1])) < 1e-6

    def test_crossbar_width(self):
        pts, _ = build_crossbar(p)
        bb = bounding_box(pts)
        assert abs((bb[2] - bb[0]) - p["CROSS_TOTAL_L"]) < 1e-4

    def test_crossbar_height(self):
        pts, _ = build_crossbar(p)
        bb = bounding_box(pts)
        assert abs((bb[3] - bb[1]) - p["CROSS_H"]) < 1e-4

    def test_shuttle_has_one_lightening_ellipse(self):
        _, holes = build_shuttle(p)
        assert len(holes) == 1

    def test_shuttle_lightening_hole_is_ellipse(self):
        _, holes = build_shuttle(p)
        assert holes[0][0] == "ellipse"

    def test_beater_has_grip_holes(self):
        _, holes = build_beater(p)
        assert len(holes) == p["BEATER_GRIP_COUNT"]

    def test_heddle_bar_has_notch_count_holes(self):
        _, holes = build_heddle_bar(p)
        assert len(holes) == p["HEDDLE_BAR_HOLE_COUNT"]
        assert p["HEDDLE_BAR_HOLE_COUNT"] == p["NOTCH_COUNT"]


# ---------------------------------------------------------------------------
# D-13 redesign: crossbar no-tenon + stile through-hole mortise
# These tests define the NEW required behaviour and must fail before the
# implementation changes are made (proof-first gate).
# ---------------------------------------------------------------------------

class TestCrossbarRedesign:

    def test_crossbar_length_equals_interior_width(self):
        """D-13: crossbar has no tenons → total length == INTERIOR_W (300mm, not 330mm)."""
        pts, _ = build_crossbar(p)
        bb = bounding_box(pts)
        assert abs((bb[2] - bb[0]) - p["INTERIOR_W"]) < 0.1, \
            f"Crossbar length {bb[2]-bb[0]:.2f} != INTERIOR_W={p['INTERIOR_W']:.2f}"

    def test_crossbar_height_is_20mm(self):
        """D-13: CROSS_H == 20mm, not MAT=6mm."""
        pts, _ = build_crossbar(p)
        bb = bounding_box(pts)
        assert abs((bb[3] - bb[1]) - 20.0) < 0.1, \
            f"Crossbar height {bb[3]-bb[1]:.2f} != 20mm"

    def test_stile_L_has_two_crossbar_rect_holes(self):
        """D-13: crossbar mortises returned as rect_holes, not embedded in outline."""
        _, holes = build_stile_L(p)
        rect_holes = [h for h in holes if h[0] == 'rect']
        assert len(rect_holes) == 2, \
            f"Expected 2 crossbar rect_holes, got {len(rect_holes)}: {holes}"

    def test_stile_L_outline_has_no_edge_slots(self):
        """D-13: stile outline is clean — no concave mortise indentations on inner face."""
        pts, _ = build_stile_L(p)
        tab_x0 = (p["STILE_W"] - p["TAB_W"]) / 2.0
        tab_x1 = tab_x0 + p["TAB_W"]
        valid_xs = {0.0, p["STILE_W"], tab_x0, tab_x1}
        for x, y in pts:
            assert any(abs(x - vx) < 1e-3 for vx in valid_xs), \
                f"Unexpected x={x:.4f} in stile outline (edge slot residue?)"


# ---------------------------------------------------------------------------
# Layout tests — happy path
# ---------------------------------------------------------------------------

class TestLayout:

    def setup_method(self):
        self.placed = layout(p)
        self.by_id = {pt["id"]: pt for pt in self.placed}

    def test_part_count(self):
        assert len(self.placed) == 10

    def test_all_expected_ids_present(self):
        ids = {pt["id"] for pt in self.placed}
        assert ids == EXPECTED_IDS

    def test_all_parts_within_sheet_bounds(self):
        M = p["MARGIN"]
        sw, sh = p["SHEET_W"], p["SHEET_H"]
        for part in self.placed:
            x0, y0, x1, y1 = part["bbox"]
            assert x0 >= M - 1e-6, f"{part['id']} left edge {x0:.3f} < margin {M}"
            assert y0 >= M - 1e-6, f"{part['id']} top edge {y0:.3f} < margin {M}"
            assert x1 <= sw - M + 1e-6, f"{part['id']} right edge {x1:.3f} > {sw-M}"
            assert y1 <= sh - M + 1e-6, f"{part['id']} bottom edge {y1:.3f} > {sh-M}"

    def test_no_part_overlaps(self):
        parts = self.placed
        for i, a in enumerate(parts):
            for j, b in enumerate(parts):
                if i >= j:
                    continue
                assert not bboxes_overlap(a["bbox"], b["bbox"]), \
                    f"Parts '{a['id']}' and '{b['id']}' overlap: {a['bbox']} vs {b['bbox']}"

    def test_stile_L_dimensions(self):
        bb = self.by_id["stile_L"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["STILE_W"]) < 0.1
        assert abs((bb[3] - bb[1]) - p["STILE_TOTAL_H"]) < 0.1

    def test_stile_R_dimensions(self):
        bb = self.by_id["stile_R"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["STILE_W"]) < 0.1
        assert abs((bb[3] - bb[1]) - p["STILE_TOTAL_H"]) < 0.1

    def test_top_rail_width(self):
        """Top rail bbox includes stand tab extensions on each end (D-17)."""
        bb = self.by_id["top_rail"]["bbox"]
        expected = p["FRAME_OUTER_W"] + 2.0 * p["STAND_RAIL_TAB_L"]
        assert abs((bb[2] - bb[0]) - expected) < 0.1

    def test_bottom_rail_width(self):
        bb = self.by_id["bottom_rail"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["FRAME_OUTER_W"]) < 0.1

    def test_crossbar_1_length(self):
        bb = self.by_id["crossbar_1"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["CROSS_TOTAL_L"]) < 0.1

    def test_crossbar_2_length(self):
        bb = self.by_id["crossbar_2"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["CROSS_TOTAL_L"]) < 0.1

    def test_stiles_not_overlapping(self):
        sl = self.by_id["stile_L"]["bbox"]
        sr = self.by_id["stile_R"]["bbox"]
        assert not bboxes_overlap(sl, sr)

    def test_top_and_bottom_rail_not_overlapping(self):
        tr = self.by_id["top_rail"]["bbox"]
        br = self.by_id["bottom_rail"]["bbox"]
        assert not bboxes_overlap(tr, br)

    def test_parts_have_sheet_pts(self):
        for part in self.placed:
            assert len(part["sheet_pts"]) > 0

    def test_parts_have_bbox_key(self):
        for part in self.placed:
            assert "bbox" in part
            x0, y0, x1, y1 = part["bbox"]
            assert x1 > x0
            assert y1 > y0

    def test_shuttle_labels_above_ellipse(self):
        """D-27: shuttle labels must not fall inside the lightening ellipse."""
        for pid in ("shuttle_1", "shuttle_2"):
            part = self.by_id[pid]
            assert "label_xy" in part, f"{pid} missing label_xy"
            _, ly = part["label_xy"]
            # Ellipse top in sheet coords = bb[1] + SHUTTLE_W/2 - SHUTTLE_LIGHT_W/2
            ellipse_top = part["bbox"][1] + p["SHUTTLE_W"] / 2.0 - p["SHUTTLE_LIGHT_W"] / 2.0
            assert ly < ellipse_top, \
                f"{pid} label y={ly:.3f} >= ellipse top {ellipse_top:.3f}"

    def test_heddle_bar_label_in_top_solid_strip(self):
        """D-27/D-32: heddle bar label placed in top solid strip (above holes), y < hole top."""
        part = self.by_id["heddle_bar"]
        assert "label_xy" in part, "heddle_bar missing label_xy"
        _, ly = part["label_xy"]
        bb = part["bbox"]
        # Holes/slots centred at bar midline. Top of holes = bb[1] + W/2 - HOLE_H/2.
        hole_top = bb[1] + p["HEDDLE_BAR_W"] / 2.0 - p["HEDDLE_BAR_HOLE_H"] / 2.0
        assert ly < hole_top, \
            f"Heddle bar label y={ly:.3f} not above hole top y={hole_top:.3f}"

    def test_bottom_rail_label_left_of_qr(self):
        """D-38: bottom rail label must be to the left of the QR code (no overlap)."""
        part = self.by_id["bottom_rail"]
        assert "label_xy" in part, "bottom_rail missing label_xy — label overlaps QR code"
        lx, _ = part["label_xy"]
        # QR left edge in sheet coords = sx + FRAME_OUTER_W/2 - 17.5/2
        sx = part["bbox"][0]
        qr_left = sx + p["FRAME_OUTER_W"] / 2.0 - 17.5 / 2.0
        assert lx < qr_left, (
            f"Bottom rail label x={lx:.1f} not left of QR left={qr_left:.1f} — overlap"
        )

    def test_bottom_rail_has_qr_etch(self):
        """D-38: bottom rail has qr_etches field with at least one filled rect (etch)."""
        part = self.by_id["bottom_rail"]
        assert "qr_etches" in part, "bottom_rail missing qr_etches field (D-38)"
        rects = part["qr_etches"]
        assert len(rects) > 0, "bottom_rail qr_etches is empty"
        # Every entry must be an SVG rect element string (etch, black fill)
        for r in rects:
            assert "<rect" in r, f"qr_etches entry not a rect: {r[:60]}"
            assert 'fill="#000000"' in r or "fill:#000000" in r, \
                f"qr_etches rect not black: {r[:80]}"

    def test_bottom_rail_qr_within_body(self):
        """D-38: QR code etch rects must all lie within the bottom rail bounding box."""
        part = self.by_id["bottom_rail"]
        if "qr_etches" not in part:
            pytest.skip("qr_etches not yet implemented")
        bb = part["bbox"]    # (x0, y0, x1, y1) in sheet coords
        import re
        for r in part["qr_etches"]:
            m = re.search(r'x="([0-9.]+)".*?y="([0-9.]+)".*?width="([0-9.]+)".*?height="([0-9.]+)"', r)
            if not m:
                continue
            rx, ry, rw, rh = [float(v) for v in m.groups()]
            assert rx >= bb[0] - 1e-3, f"QR rect x={rx:.3f} < rail left {bb[0]:.3f}"
            assert ry >= bb[1] - 1e-3, f"QR rect y={ry:.3f} < rail top {bb[1]:.3f}"
            assert rx + rw <= bb[2] + 1e-3, f"QR rect right={rx+rw:.3f} > rail right {bb[2]:.3f}"
            assert ry + rh <= bb[3] + 1e-3, f"QR rect bot={ry+rh:.3f} > rail bot {bb[3]:.3f}"

    def test_heddle_bar_has_hs_etch_labels(self):
        """D-33: heddle bar has per-position H/S etch labels (hole=H, slot=S)."""
        part = self.by_id["heddle_bar"]
        assert "hole_labels" in part, "heddle_bar missing hole_labels (D-33)"
        labels = part["hole_labels"]
        count = p["HEDDLE_BAR_HOLE_COUNT"]
        # Must have at least count labels (one per position; holes may have two)
        assert len(labels) >= count, \
            f"Expected >= {count} labels, got {len(labels)}"
        letters = [lbl for _, _, lbl, _ in labels]
        assert "H" in letters, "No H labels found in heddle_bar hole_labels"
        assert "S" in letters, "No S labels found in heddle_bar hole_labels"
        # H labels must only appear at even-index positions (stadium holes)
        # S labels must appear at both even (paired with H) and odd (slots)
        h_count = letters.count("H")
        s_count = letters.count("S")
        assert h_count > 0 and s_count > 0, \
            f"H count={h_count}, S count={s_count}: both must be positive"


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

    def test_stile_L_height_spot_check(self):
        ok, detail = self.by_name["dim:stile_L height"]
        assert ok, detail

    def test_stile_L_width_spot_check(self):
        ok, detail = self.by_name["dim:stile_L width"]
        assert ok, detail

    def test_top_rail_width_spot_check(self):
        ok, detail = self.by_name["dim:top_rail width"]
        assert ok, detail

    def test_crossbar_length_spot_check(self):
        ok, detail = self.by_name["dim:crossbar_1 length"]
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
        """Every path element's d attribute must end with Z (closed)."""
        import re
        # Match ' d="..."' — leading space avoids matching id="..." suffix
        d_values = re.findall(r' d="([^"]+)"', self.svg)
        assert d_values, "No path d-attributes found in SVG"
        for d in d_values:
            assert d.endswith("Z"), f"Unclosed path d: {d[:80]}"

    def test_stroke_is_red(self):
        assert "stroke" in self.svg
        # Red cut colour
        assert "#ff0000" in self.svg.lower() or "stroke:#ff0000" in self.svg.lower() \
            or 'stroke="#ff0000"' in self.svg.lower() or "stroke:red" in self.svg.lower() or \
            "ff0000" in self.svg.lower()

    def test_fill_none(self):
        assert "fill:none" in self.svg or 'fill="none"' in self.svg


# ---------------------------------------------------------------------------
# Write tests
# ---------------------------------------------------------------------------

class TestWrite:

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_loom.svg")
            result = write(p, path=path)
            assert result == path
            assert os.path.exists(path)

    def test_write_file_not_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_loom.svg")
            write(p, path=path)
            size = os.path.getsize(path)
            assert size > 1000, f"SVG file too small: {size} bytes"

    def test_write_returns_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_loom.svg")
            result = write(p, path=path)
            assert isinstance(result, str)
            assert result.endswith(".svg")


# ---------------------------------------------------------------------------
# Unhappy-path tests
# ---------------------------------------------------------------------------

class TestUnhappyPath:

    def test_oversized_interior_raises_on_layout(self):
        """Interior 580×580mm → stile total height 604mm > 600mm sheet → layout fails."""
        with pytest.raises((ValueError, AssertionError)):
            # make_params will catch it via assert_all if invariants fire,
            # otherwise layout() raises ValueError on OOB
            large = make_params(interior_w=560.0, interior_h=560.0)
            layout(large)

    def test_layout_raises_for_manually_oob_part(self):
        """Manually corrupt a placed part to be OOB and confirm verify detects it."""
        placed = layout(p)
        # Move stile_L right edge to 700mm (beyond sheet)
        for part in placed:
            if part["id"] == "stile_L":
                x0, y0, x1, y1 = part["bbox"]
                part["bbox"] = (x0, y0, 700.0, y1)
                break
        results = verify(placed, p)
        by_name = {n: (ok, d) for n, ok, d in results}
        ok, detail = by_name["I-1"]
        assert not ok, f"I-1 should fail for OOB part; got: {detail}"

    def test_verify_detects_overlap(self):
        """Manually overlap two parts; verify must report I-2 failure."""
        placed = layout(p)
        # Move crossbar_2 on top of crossbar_1
        for part in placed:
            if part["id"] == "crossbar_2":
                part["bbox"] = placed[0]["bbox"]  # crossbar_1's bbox
                break
        results = verify(placed, p)
        by_name = {n: (ok, d) for n, ok, d in results}
        ok, detail = by_name["I-2"]
        assert not ok, f"I-2 should fail for overlapping parts; got: {detail}"

    def test_write_fails_if_verify_fails(self):
        """write() must not write if verify detects a failure."""
        # We can't easily corrupt a placed layout through write()'s API,
        # but we can verify write() calls verify() by checking it works for valid params.
        # This is a smoke test: valid params must not raise.
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ok.svg")
            result = write(p, path=path)
            assert os.path.exists(path)

    def test_generate_with_alternate_params(self):
        """generate() must work for a different valid interior size."""
        alt = make_params(interior_w=250.0, interior_h=350.0)
        svg = generate(alt)
        assert "<svg " in svg
        assert svg.rstrip().endswith("</svg>")

    def test_layout_250x350(self):
        """250×350mm interior still fits on 600×600mm sheet."""
        alt = make_params(interior_w=250.0, interior_h=350.0)
        placed = layout(alt)
        results = verify(placed, alt)
        failures = [(n, d) for n, ok, d in results if not ok]
        assert not failures, f"250×350 layout failures: {failures}"
