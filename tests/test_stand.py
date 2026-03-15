"""
tests/test_stand.py — 2-piece triangular X easel stand (src/stand.py), D-23.

D-23: Two identical 6mm ply pieces (right triangles), cross-halving joint at centre.
Piece B is piece A flipped horizontally for assembly.

Piece geometry (piece-local coords, L=STAND_X_L, W=STAND_X_W):
  Right triangle: (0,0), (L,0), (0,W). 12-point polygon with:
    1. Cross-halving slot from top (y=0) at x=L/2, width=SLOT_W, depth=W/4.
    2. Foot ledge: protrudes +y from foot corner, TAB_H above ground × TAB_L deep.
    3. Bump: step at outer ledge end, BUMP_H tall × BUMP_L deep.
"""

import re
import os
import sys
import math
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT as p
from src.geometry import bounding_box, bboxes_overlap

from src.stand import (
    build_stand_x_piece,
    build_stand_x_piece_b,
    layout,
    render,
    verify,
    generate,
    write,
)

EXPECTED_IDS = {"stand_x_a", "stand_x_b"}


# ---------------------------------------------------------------------------
# Part builder tests
# ---------------------------------------------------------------------------

class TestBuildStandXPiece:

    def setup_method(self):
        self.pts, self.holes = build_stand_x_piece(p)
        self.bb = bounding_box(self.pts)

    def test_no_holes(self):
        """X piece has no separate hole paths — all features are polygon vertices."""
        assert self.holes == []

    def test_polygon_point_count(self):
        """Triangular piece polygon has 12 points (slot 4 + blunt tip 2 + hyp-to-tab 1 + tab+bump 4 + return 1)."""
        assert len(self.pts) == 12, f"Expected 12 pts, got {len(self.pts)}: {self.pts}"

    def test_bounding_box_length(self):
        """Piece bbox width = STAND_X_L - tip_blunt_x (sharp tip replaced by flat blunt end, D-28)."""
        tip_blunt_x = p["STAND_X_TIP_W"] * p["STAND_X_L"] / p["STAND_X_W"]
        expected_w = p["STAND_X_L"] - tip_blunt_x
        actual_w = self.bb[2] - self.bb[0]
        assert abs(actual_w - expected_w) < 0.1, \
            f"bbox width={actual_w:.3f} != L-tip_blunt_x={expected_w:.3f}"

    def test_bounding_box_height(self):
        """Piece bbox height = STAND_X_W + STAND_X_TAB_L + STAND_X_BUMP_L (+y ledge protrusion)."""
        expected_h = p["STAND_X_W"] + p["STAND_X_TAB_L"] + p["STAND_X_BUMP_L"]
        actual_h = self.bb[3] - self.bb[1]
        assert abs(actual_h - expected_h) < 0.1, \
            f"bbox height={actual_h:.3f} != W+TAB_L+BUMP_L={expected_h}"

    def test_tip_blunted(self):
        """D-28: tip blunted — no point at x=STAND_X_L; max_x = L - tip_blunt_x."""
        L = p["STAND_X_L"]
        tip_blunt_x = p["STAND_X_TIP_W"] * L / p["STAND_X_W"]
        sharp_tip = [pt for pt in self.pts if abs(pt[0] - L) < 1e-6]
        assert len(sharp_tip) == 0, f"Sharp tip at x=L still present: {sharp_tip}"
        xs = [pt[0] for pt in self.pts]
        assert abs(max(xs) - (L - tip_blunt_x)) < 0.1, \
            f"max_x={max(xs):.3f} != L-tip_blunt_x={L-tip_blunt_x:.3f}"

    def test_tab_hyp_intercept_inside_triangle(self):
        """Tab connects to hyp at (TAB_H, hyp_y_at_TAB_H) — y < W, inside triangle body, not at corner."""
        TAB_H = p["STAND_X_TAB_H"]
        W = p["STAND_X_W"]
        L = p["STAND_X_L"]
        hyp_y = W * (1.0 - TAB_H / L)
        intercept = [pt for pt in self.pts if abs(pt[0] - TAB_H) < 1e-6]
        assert len(intercept) >= 2, f"Expected >=2 pts at x=TAB_H={TAB_H}; got {intercept}"
        min_y = min(pt[1] for pt in intercept)
        assert min_y < W - 1e-6, \
            f"Tab inner y={min_y:.3f} must be < W={W} (connected along hyp body, not corner)"
        assert abs(min_y - hyp_y) < 0.5, \
            f"Tab inner y={min_y:.3f} should equal hyp_y={hyp_y:.3f} at x=TAB_H"

    def test_cross_halving_slot_centred(self):
        """Slot centred at x = STAND_X_L / 2."""
        slot_d = p["STAND_X_SLOT_D"]
        cx = p["STAND_X_L"] / 2.0
        depth_pts = sorted(
            [pt for pt in self.pts if abs(pt[1] - slot_d) < 1e-6],
            key=lambda pt: pt[0],
        )
        assert len(depth_pts) >= 2, f"No points at slot_d y={slot_d}"
        measured_cx = (depth_pts[0][0] + depth_pts[-1][0]) / 2.0
        assert abs(measured_cx - cx) < 0.1, \
            f"Slot centre x={measured_cx:.3f} != L/2={cx}"

    def test_cross_halving_slot_width(self):
        """Slot is STAND_X_SLOT_W wide."""
        slot_d = p["STAND_X_SLOT_D"]
        slot_w = p["STAND_X_SLOT_W"]
        depth_pts = sorted(
            [pt for pt in self.pts if abs(pt[1] - slot_d) < 1e-6],
            key=lambda pt: pt[0],
        )
        assert len(depth_pts) >= 2, "No slot depth points"
        measured_w = depth_pts[-1][0] - depth_pts[0][0]
        assert abs(measured_w - slot_w) < 0.1, \
            f"Slot width={measured_w:.3f} != SLOT_W={slot_w}"

    def test_slot_depth_is_quarter_width(self):
        """Slot depth = STAND_X_W / 4 (half of triangle height at slot x = L/2)."""
        expected = p["STAND_X_W"] / 4.0
        assert abs(p["STAND_X_SLOT_D"] - expected) < 0.1, \
            f"STAND_X_SLOT_D={p['STAND_X_SLOT_D']:.3f} != W/4={expected:.3f}"

    def test_slot_within_triangle_body(self):
        """Slot bottom is below the hypotenuse at that x (slot doesn't escape the piece)."""
        slot_d = p["STAND_X_SLOT_D"]
        slot_cx = p["STAND_X_L"] / 2.0
        # Triangle height at slot_cx: W × (1 − slot_cx/L)
        triangle_h_at_cx = p["STAND_X_W"] * (1.0 - slot_cx / p["STAND_X_L"])
        assert slot_d < triangle_h_at_cx - 1e-6, \
            f"Slot_d={slot_d:.3f} not < triangle_h={triangle_h_at_cx:.3f} at x={slot_cx}"

    def test_slot_concave_from_top(self):
        """No slot point at y < 0 — slot is concave from top edge."""
        ys = [pt[1] for pt in self.pts]
        assert min(ys) >= -1e-9, f"Point below y=0: min y={min(ys):.4f}"

    def test_no_minus_x_protrusion(self):
        """Tab does not protrude in -x: no point at x < 0 (old underground tab gone)."""
        xs = [pt[0] for pt in self.pts]
        assert min(xs) >= -1e-6, f"Unexpected -x protrusion: min x={min(xs):.4f}"

    def test_tab_protrudes_in_plus_y(self):
        """Tab protrudes in +y beyond STAND_X_W (outward from foot end when standing)."""
        W = p["STAND_X_W"]
        ys = [pt[1] for pt in self.pts]
        assert max(ys) > W + 1e-6, \
            f"No +y protrusion past W={W}: max y={max(ys):.4f}"

    def test_ledge_face_at_tab_h(self):
        """Ledge face spans from hyp intercept to tab outer, both at x=STAND_X_TAB_H."""
        TAB_H = p["STAND_X_TAB_H"]
        TAB_L = p["STAND_X_TAB_L"]
        W = p["STAND_X_W"]
        L = p["STAND_X_L"]
        hyp_y = W * (1.0 - TAB_H / L)
        ledge_pts = [pt for pt in self.pts if abs(pt[0] - TAB_H) < 1e-6]
        assert len(ledge_pts) >= 2, \
            f"Expected ≥2 pts at x=TAB_H={TAB_H}; got {ledge_pts}"
        ys = sorted(pt[1] for pt in ledge_pts)
        assert abs(ys[-1] - (hyp_y + TAB_L)) < 0.5, \
            f"Ledge outer y={ys[-1]:.3f} should equal hyp_y+TAB_L={hyp_y+TAB_L:.3f}"

    def test_ledge_depth_fits_rail(self):
        """Ledge clear depth (TAB_L) >= RAIL_W so loom bottom rail fits on ledge."""
        assert p["STAND_X_TAB_L"] >= p["RAIL_W"], \
            f"TAB_L={p['STAND_X_TAB_L']} < RAIL_W={p['RAIL_W']}: rail won't fit on ledge"

    def test_bump_above_ledge(self):
        """Bump face at x=TAB_H+BUMP_H; inner y = hyp_y_at_TAB_H + TAB_L."""
        TAB_H = p["STAND_X_TAB_H"]
        BUMP_H = p["STAND_X_BUMP_H"]
        TAB_L = p["STAND_X_TAB_L"]
        W = p["STAND_X_W"]
        L = p["STAND_X_L"]
        hyp_y = W * (1.0 - TAB_H / L)
        expected_bump_inner_y = hyp_y + TAB_L
        bump_top_x = TAB_H + BUMP_H
        bump_pts = [pt for pt in self.pts if abs(pt[0] - bump_top_x) < 1e-6]
        assert len(bump_pts) >= 2, \
            f"Expected ≥2 pts at bump x={bump_top_x}; got {bump_pts}"
        ys = sorted(pt[1] for pt in bump_pts)
        assert abs(ys[0] - expected_bump_inner_y) < 0.5, \
            f"Bump inner y={ys[0]:.3f} should equal hyp_y+TAB_L={expected_bump_inner_y:.3f}"

    def test_tab_outer_face_at_ground(self):
        """Return point at x=0, y=W+TAB_L+BUMP_L closes tab back to foot edge."""
        W = p["STAND_X_W"]
        TAB_L = p["STAND_X_TAB_L"]
        BUMP_L = p["STAND_X_BUMP_L"]
        outer_y = W + TAB_L + BUMP_L
        outer_pts = [pt for pt in self.pts if abs(pt[1] - outer_y) < 1e-6 and abs(pt[0]) < 1e-6]
        assert len(outer_pts) >= 1, \
            f"Expected return point at x=0, y={outer_y}, got {outer_pts}"


# ---------------------------------------------------------------------------
# Piece B — slot from hypotenuse (mating cross-halving joint)
# ---------------------------------------------------------------------------

class TestBuildStandXPieceB:

    def setup_method(self):
        self.pts_a, _ = build_stand_x_piece(p)
        self.pts_b, _ = build_stand_x_piece_b(p)

    def test_piece_b_top_edge_no_slot(self):
        """Piece B top edge (y=0): only x=0 (foot) and x=L-tip_blunt_x (blunted tip, D-28)."""
        L = p["STAND_X_L"]
        tip_blunt_x = p["STAND_X_TIP_W"] * L / p["STAND_X_W"]
        top_pts = [(x, y) for x, y in self.pts_b if abs(y) < 1e-6]
        xs = sorted(x for x, y in top_pts)
        assert len(top_pts) == 2, \
            f"Expected 2 pts at y=0 (foot top and blunted tip), got {len(top_pts)}: {top_pts}"
        assert abs(xs[0]) < 1e-6, f"Expected x=0 at foot top, got {xs[0]:.3f}"
        assert abs(xs[1] - (L - tip_blunt_x)) < 0.1, \
            f"Expected x=L-tip_blunt_x={L-tip_blunt_x:.3f} at blunted tip, got {xs[1]:.3f}"

    def test_piece_b_slot_bottom_at_slot_d(self):
        """Piece B slot bottom is at y=STAND_X_SLOT_D (same as piece A — slots mate there)."""
        slot_d = p["STAND_X_SLOT_D"]
        slot_cx = p["STAND_X_L"] / 2.0
        slot_w = p["STAND_X_SLOT_W"]
        bottom_pts = [
            (x, y) for x, y in self.pts_b
            if abs(y - slot_d) < 0.5 and (slot_cx - slot_w) < x < (slot_cx + slot_w)
        ]
        assert len(bottom_pts) >= 2, \
            f"Expected ≥2 slot-bottom pts at y≈{slot_d} near x={slot_cx}, got {bottom_pts}"

    def test_piece_b_has_hyp_slot_points(self):
        """Piece B has points at the hypotenuse y-values where the slot opens."""
        slot_cx = p["STAND_X_L"] / 2.0
        slot_w = p["STAND_X_SLOT_W"]
        L = p["STAND_X_L"]
        W = p["STAND_X_W"]
        hyp_y_left  = W * (1.0 - (slot_cx - slot_w / 2.0) / L)
        hyp_y_right = W * (1.0 - (slot_cx + slot_w / 2.0) / L)
        hyp_pts = [
            (x, y) for x, y in self.pts_b
            if (
                (abs(x - (slot_cx - slot_w / 2.0)) < 0.1 and abs(y - hyp_y_left)  < 0.5)
                or
                (abs(x - (slot_cx + slot_w / 2.0)) < 0.1 and abs(y - hyp_y_right) < 0.5)
            )
        ]
        assert len(hyp_pts) >= 2, \
            f"Expected ≥2 pts at hyp y near slot (≈{hyp_y_right:.1f}–{hyp_y_left:.1f}), got {hyp_pts}"

    def test_slots_mate_no_gap_no_overlap(self):
        """At x=L/2: piece A slot covers y=0..slot_d; piece B slot covers slot_d..hyp_y; no gap."""
        slot_d = p["STAND_X_SLOT_D"]
        slot_cx = p["STAND_X_L"] / 2.0
        L = p["STAND_X_L"]
        W = p["STAND_X_W"]
        hyp_y = W * (1.0 - slot_cx / L)  # = W/2 = 40mm
        # Piece A: slot y=0..slot_d; material y=slot_d..hyp_y
        # Piece B: slot y=slot_d..hyp_y; material y=0..slot_d
        # Together: slot_d (A bottom) == slot_d (B top): no gap, no overlap
        assert abs(hyp_y - 2.0 * slot_d) < 1e-6, \
            f"hyp_y={hyp_y:.3f} != 2×slot_d={2*slot_d:.3f}: slots will not fully mate"


# ---------------------------------------------------------------------------
# Param sanity tests
# ---------------------------------------------------------------------------

class TestStandXParams:

    def test_slot_w_is_clearance_fit(self):
        """STAND_X_SLOT_W = MAT + 0.1mm clearance (cross-halving fit)."""
        expected = p["MAT"] + 0.1
        assert abs(p["STAND_X_SLOT_W"] - expected) < 0.05

    def test_slot_d_is_quarter_width(self):
        """STAND_X_SLOT_D = STAND_X_W / 4 (half of triangle height at slot_cx = L/2)."""
        expected = p["STAND_X_W"] / 4.0
        assert abs(p["STAND_X_SLOT_D"] - expected) < 0.1

    def test_stand_x_l_present(self):
        """D-29: STAND_X_L = FRAME_OUTER_H (= interior_h + 2×rail_w)."""
        assert "STAND_X_L" in p
        assert abs(p["STAND_X_L"] - p["FRAME_OUTER_H"]) < 0.1, \
            f"STAND_X_L={p['STAND_X_L']}, expected FRAME_OUTER_H={p['FRAME_OUTER_H']}"

    def test_stand_x_tab_l_is_30mm(self):
        """D-23: STAND_X_TAB_L = 30mm (RAIL_W=22mm + 8mm clearance for secure rail seating)."""
        assert "STAND_X_TAB_L" in p
        assert abs(p["STAND_X_TAB_L"] - 30.0) < 1e-9

    def test_stand_corner_r_in_params(self):
        """D-28: STAND_X_CORNER_R = 0mm — tip squared off only; other corners straight."""
        assert "STAND_X_CORNER_R" in p, "STAND_X_CORNER_R missing from params"
        assert abs(p["STAND_X_CORNER_R"] - 0.0) < 1e-9

    def test_stand_tip_w_in_params(self):
        """D-28: STAND_X_TIP_W = 10mm — blunt-end flat width at triangle tip."""
        assert "STAND_X_TIP_W" in p, "STAND_X_TIP_W missing from params"
        assert abs(p["STAND_X_TIP_W"] - 10.0) < 0.1

    def test_stand_x_bump_l_present(self):
        """D-23: STAND_X_BUMP_L present and ~5mm."""
        assert "STAND_X_BUMP_L" in p
        assert 2.0 <= p["STAND_X_BUMP_L"] <= 10.0

    def test_rail_notch_params_removed(self):
        """D-23: STAND_X_RAIL_NOTCH_W/D removed (replaced by foot tab)."""
        assert "STAND_X_RAIL_NOTCH_W" not in p, "STAND_X_RAIL_NOTCH_W should be removed in D-23"
        assert "STAND_X_RAIL_NOTCH_D" not in p, "STAND_X_RAIL_NOTCH_D should be removed in D-23"

    def test_pieces_fit_in_box_length(self):
        """STAND_X_L < BOX_INTERIOR_L (piece body fits lengthwise; tab protrusion is SHOULD/COULD)."""
        assert p["STAND_X_L"] < p["BOX_INTERIOR_L"], \
            f"STAND_X_L={p['STAND_X_L']} >= BOX_INTERIOR_L={p['BOX_INTERIOR_L']}"

    def test_two_pieces_fit_in_box_width(self):
        """2 × STAND_X_W + 2mm gap < BOX_INTERIOR_W (flat-pack in box layer 2)."""
        two_w = 2.0 * p["STAND_X_W"] + 2.0
        assert two_w < p["BOX_INTERIOR_W"], \
            f"2×STAND_X_W+gap={two_w} >= BOX_INTERIOR_W={p['BOX_INTERIOR_W']}"


# ---------------------------------------------------------------------------
# Layout tests
# ---------------------------------------------------------------------------

class TestLayout:

    def setup_method(self):
        self.placed = layout(p)
        self.by_id = {pt["id"]: pt for pt in self.placed}

    def test_part_count(self):
        """Layout produces exactly 2 parts."""
        assert len(self.placed) == 2, f"Expected 2 parts, got {len(self.placed)}"

    def test_all_expected_ids_present(self):
        ids = {pt["id"] for pt in self.placed}
        assert ids == EXPECTED_IDS

    def test_all_parts_within_sheet_bounds(self):
        M = p["MARGIN"]
        sw, sh = p["SHEET_W"], p["SHEET_H"]
        for part in self.placed:
            x0, y0, x1, y1 = part["bbox"]
            assert x0 >= M - 1e-6, f"{part['id']} left {x0:.3f} < margin"
            assert y0 >= M - 1e-6, f"{part['id']} top  {y0:.3f} < margin"
            assert x1 <= sw - M + 1e-6, f"{part['id']} right  {x1:.3f} > {sw-M}"
            assert y1 <= sh - M + 1e-6, f"{part['id']} bottom {y1:.3f} > {sh-M}"

    def test_no_part_overlaps(self):
        parts = self.placed
        for i, a in enumerate(parts):
            for j, b in enumerate(parts):
                if i >= j:
                    continue
                assert not bboxes_overlap(a["bbox"], b["bbox"]), \
                    f"'{a['id']}' and '{b['id']}' overlap"

    def test_both_pieces_same_bounding_box_size(self):
        """Both pieces have the same bounding box dimensions."""
        bbs = [self.by_id[pid]["bbox"] for pid in ["stand_x_a", "stand_x_b"]]
        for dim in (0, 1):  # width, height
            sizes = [(bb[2+dim] - bb[dim]) for bb in bbs]
            assert abs(sizes[0] - sizes[1]) < 0.1, \
                f"Part bbox dim {dim} differs: {sizes}"

    def test_piece_bbox_width(self):
        """Each piece bbox width = L - tip_blunt_x (blunted tip, D-28)."""
        L = p["STAND_X_L"]
        tip_blunt_x = p["STAND_X_TIP_W"] * L / p["STAND_X_W"]
        expected_w = L - tip_blunt_x
        for pid in ["stand_x_a", "stand_x_b"]:
            bb = self.by_id[pid]["bbox"]
            w = bb[2] - bb[0]
            assert abs(w - expected_w) < 0.1, \
                f"{pid} bbox width={w:.2f} != L-tip_blunt_x={expected_w:.2f}"

    def test_piece_bbox_height(self):
        """Each piece bbox height = STAND_X_W + STAND_X_TAB_L + STAND_X_BUMP_L (+y ledge)."""
        expected_h = p["STAND_X_W"] + p["STAND_X_TAB_L"] + p["STAND_X_BUMP_L"]
        for pid in ["stand_x_a", "stand_x_b"]:
            bb = self.by_id[pid]["bbox"]
            h = bb[3] - bb[1]
            assert abs(h - expected_h) < 0.1, f"{pid} bbox height={h:.2f} != {expected_h}"

    def test_pieces_stacked_vertically(self):
        """Pieces are placed at different y positions."""
        bb_a = self.by_id["stand_x_a"]["bbox"]
        bb_b = self.by_id["stand_x_b"]["bbox"]
        assert abs(bb_a[1] - bb_b[1]) > 1.0, "Pieces at same y position"


# ---------------------------------------------------------------------------
# Verify / generate / write tests
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


class TestGenerate:

    def test_returns_string(self):
        assert isinstance(generate(p), str)

    def test_contains_svg_tag(self):
        assert "<svg " in generate(p)

    def test_all_paths_closed(self):
        svg = generate(p)
        paths = re.findall(r' d="([^"]+)"', svg)
        assert paths
        open_paths = [d[:60] for d in paths if not d.rstrip().endswith("Z")]
        assert open_paths == [], f"Open paths: {open_paths}"

    def test_svg_outer_paths_no_arcs(self):
        """D-28: stand outer paths have no arc commands — tip squared off as flat cut, other corners straight."""
        svg = generate(p)
        paths = re.findall(r' d="([^"]+)"', svg)
        arc_paths = [d for d in paths if " A " in d]
        assert not arc_paths, f"Unexpected arc commands in stand SVG: {arc_paths}"

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "optional_loom_stand.svg")
            result = write(p, path=path)
            assert result == path
            assert os.path.exists(path)
            assert os.path.getsize(path) > 200
