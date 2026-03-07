"""
tests/test_stand.py — Triangle stand generator (src/stand.py), D-18.

D-18: Solid right-triangle side pieces + 5 cross members.
Parts: Stand-L, Stand-R, rear_cross_1/2/3 (3), base_cross_1/2 (2). Total: 7.
"""

import re
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.params import DEFAULT as p
from src.geometry import bounding_box, bboxes_overlap

from src.stand import (
    build_stand_triangle,
    build_stand_cross,
    layout,
    render,
    verify,
    generate,
    write,
)

EXPECTED_IDS = {
    "stand_L", "stand_R",
    "stand_rear_cross_1", "stand_rear_cross_2", "stand_rear_cross_3",
    "stand_base_cross_1", "stand_base_cross_2",
    "hyp_cross",
}


# ---------------------------------------------------------------------------
# Part builder tests
# ---------------------------------------------------------------------------

class TestBuildStandTriangle:

    def setup_method(self):
        self.pts, self.holes = build_stand_triangle(p)
        self.bb = bounding_box(self.pts)

    def test_bounding_box_width(self):
        """Triangle bbox width = STAND_BASE_L = 240mm."""
        w = self.bb[2] - self.bb[0]
        assert abs(w - p["STAND_BASE_L"]) < 0.1, f"bbox w={w:.2f} != {p['STAND_BASE_L']}"

    def test_bounding_box_height(self):
        """Triangle bbox height = STAND_UPRIGHT_H = 420mm."""
        h = self.bb[3] - self.bb[1]
        assert abs(h - p["STAND_UPRIGHT_H"]) < 0.1, f"bbox h={h:.2f} != {p['STAND_UPRIGHT_H']}"

    def test_no_holes(self):
        """Triangle has no rect_hole — all notches are in the outer polygon."""
        assert self.holes == []

    def test_upright_notch_depths(self):
        """3 upright notches each reach STAND_NOTCH_D from x=0 into body."""
        nd = p["STAND_NOTCH_D"]
        depth_pts = [pt for pt in self.pts if abs(pt[0] - nd) < 1e-6]
        assert len(depth_pts) >= 6, \
            f"Expected ≥6 points at notch depth x={nd} (2 per notch × 3), got {len(depth_pts)}"

    def test_upright_notch_concave(self):
        """Upright notches go INTO body (x > 0); no point at x < 0."""
        xs = [pt[0] for pt in self.pts]
        assert min(xs) >= -1e-9, f"Upright notch convex: min x={min(xs):.4f}"

    def test_base_notch_depths(self):
        """2 base notches each reach STAND_NOTCH_D up from y=STAND_UPRIGHT_H."""
        nd = p["STAND_NOTCH_D"]
        uh = p["STAND_UPRIGHT_H"]
        depth_pts = [pt for pt in self.pts if abs(pt[1] - (uh - nd)) < 1e-6]
        assert len(depth_pts) >= 4, \
            f"Expected ≥4 points at base notch depth y={uh-nd:.2f} (2 per notch × 2), got {len(depth_pts)}"

    def test_base_notch_concave(self):
        """Base notches go INTO body (y < STAND_UPRIGHT_H); no point beyond upright_h."""
        ys = [pt[1] for pt in self.pts]
        assert max(ys) <= p["STAND_UPRIGHT_H"] + 1e-9, \
            f"Base notch convex: max y={max(ys):.4f}"

    def test_five_notches_total(self):
        """Triangle has 3 upright + 2 base = 5 edge notches (polygon is non-rectangular)."""
        # Plain triangle has 3 points; each notch adds 3 more → 3 + 5*3 = 18 minimum
        assert len(self.pts) >= 18, f"Expected ≥18 pts for 5 notches, got {len(self.pts)}"

    def test_upright_notch_entry_zone(self):
        """Upright notches have L-shaped entry: points at STAND_NOTCH_ENTRY_D (partial depth). D-19."""
        entry_d = p["STAND_NOTCH_ENTRY_D"]   # KeyError until params updated
        pts_at_entry = [pt for pt in self.pts if abs(pt[0] - entry_d) < 1e-6]
        # 2 points per upright notch at entry depth (step-top and step-bot), 3 notches → ≥6
        assert len(pts_at_entry) >= 6, \
            f"Expected ≥6 pts at entry_d x={entry_d} (2 per notch × 3 notches), got {len(pts_at_entry)}"

    def test_hyp_notch_in_triangle(self):
        """Triangle has hyp-edge notch: ≥4 points not on upright/base boundary. D-19."""
        cx = p["STAND_HYP_CX"]   # KeyError until params updated
        nd = p["STAND_NOTCH_D"]
        uh = p["STAND_UPRIGHT_H"]
        # Hyp notch points: interior (x > 0, y < upright_h) and NOT at x == notch_d (upright notch pts)
        interior = [
            pt for pt in self.pts
            if pt[0] > 1e-6
            and pt[1] < uh - 1e-6
            and abs(pt[0] - nd) > 0.5
        ]
        assert len(interior) >= 4, \
            f"Expected ≥4 hyp-notch interior pts, got {len(interior)}: {interior[:6]}"

    def test_upright_notch_y_positions(self):
        """Upright notch centres at STAND_MORT_Y_TOP, STAND_MORT_Y_MID, STAND_MORT_Y_BOT."""
        nw = p["STAND_NOTCH_W"]
        nd_depth = p["STAND_NOTCH_D"]
        for key in ("STAND_MORT_Y_TOP", "STAND_MORT_Y_MID", "STAND_MORT_Y_BOT"):
            cy = p[key]
            # At notch depth, we expect two y-coords: cy-nw/2 and cy+nw/2
            pts_at_depth = [pt for pt in self.pts if abs(pt[0] - nd_depth) < 1e-6]
            ys_at_depth = {round(pt[1], 4) for pt in pts_at_depth}
            y0 = round(cy - nw / 2.0, 4)
            y1 = round(cy + nw / 2.0, 4)
            assert y0 in ys_at_depth or any(abs(y - (cy - nw/2)) < 0.1 for y in ys_at_depth), \
                f"No notch top at y={cy-nw/2:.2f} for {key}={cy}"


class TestBuildStandCross:

    def test_plain_cross_dimensions(self):
        """Cross member without stile slots: 374×30mm bounding box."""
        pts, holes = build_stand_cross(p, with_stile_slots=False)
        bb = bounding_box(pts)
        total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]
        assert abs((bb[2] - bb[0]) - total_l) < 0.1, f"width {bb[2]-bb[0]:.2f} != {total_l}"
        assert abs((bb[3] - bb[1]) - p["STAND_SPREAD_W"]) < 0.1
        assert holes == []

    def test_plain_cross_is_rectangle(self):
        """Cross without stile slots: exactly 4 polygon points."""
        pts, _ = build_stand_cross(p, with_stile_slots=False)
        assert len(pts) == 4, f"Expected 4 pts for plain rect, got {len(pts)}"

    def test_slotted_cross_dimensions(self):
        """Cross with stile slots: bounding box still 374×30mm."""
        pts, holes = build_stand_cross(p, with_stile_slots=True)
        bb = bounding_box(pts)
        total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]
        assert abs((bb[2] - bb[0]) - total_l) < 0.1
        assert abs((bb[3] - bb[1]) - p["STAND_SPREAD_W"]) < 0.1
        assert holes == []

    def test_slotted_cross_has_cutouts(self):
        """Cross with stile slots: polygon has >4 points (two concave cutouts)."""
        pts, _ = build_stand_cross(p, with_stile_slots=True)
        assert len(pts) > 4, f"Expected >4 pts for slotted cross, got {len(pts)}"

    def test_stile_slot_depth(self):
        """Stile slots reach STAND_STILE_SLOT_D from top edge (y=0)."""
        pts, _ = build_stand_cross(p, with_stile_slots=True)
        sd = p["STAND_STILE_SLOT_D"]
        depth_pts = [pt for pt in pts if abs(pt[1] - sd) < 1e-6]
        assert len(depth_pts) >= 4, \
            f"Expected ≥4 pts at slot depth y={sd}, got {len(depth_pts)}"

    def test_stile_slots_concave(self):
        """Stile slots go INTO body; no point at y < 0."""
        pts, _ = build_stand_cross(p, with_stile_slots=True)
        ys = [pt[1] for pt in pts]
        assert min(ys) >= -1e-9

    def test_stile_slot_width(self):
        """Stile slot total width = STAND_STILE_SLOT_W."""
        pts, _ = build_stand_cross(p, with_stile_slots=True)
        sd = p["STAND_STILE_SLOT_D"]
        sw = p["STAND_STILE_SLOT_W"]
        # Get x-coords of points at slot depth
        pts_at_sd = [pt for pt in pts if abs(pt[1] - sd) < 1e-6]
        # Should have 2 pairs of points (one per slot)
        xs = sorted(pt[0] for pt in pts_at_sd)
        assert len(xs) >= 4, f"Expected ≥4 points at slot depth, got {len(xs)}"
        slot1_w = xs[1] - xs[0]
        slot2_w = xs[3] - xs[2]
        assert abs(slot1_w - sw) < 0.1, f"Slot 1 width={slot1_w:.3f} != {sw}"
        assert abs(slot2_w - sw) < 0.1, f"Slot 2 width={slot2_w:.3f} != {sw}"

    def test_stile_slots_within_body(self):
        """Stile slots start at or after the tenon end (x ≥ STAND_SPREAD_TEN_L)."""
        pts, _ = build_stand_cross(p, with_stile_slots=True)
        ten_l = p["STAND_SPREAD_TEN_L"]
        sd = p["STAND_STILE_SLOT_D"]
        pts_at_sd = [pt for pt in pts if abs(pt[1] - sd) < 1e-6]
        xs = sorted(pt[0] for pt in pts_at_sd)
        assert xs[0] >= ten_l - 1e-6, \
            f"Left slot starts at x={xs[0]:.3f} before tenon end x={ten_l}"
        total_l = p["STAND_SPREAD_L"] + 2.0 * ten_l
        assert xs[-1] <= total_l - ten_l + 1e-6, \
            f"Right slot ends at x={xs[-1]:.3f} after body end x={total_l-ten_l}"


# ---------------------------------------------------------------------------
# Layout tests
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

    def test_L_R_same_bounding_box_size(self):
        bb_l = self.by_id["stand_L"]["bbox"]
        bb_r = self.by_id["stand_R"]["bbox"]
        assert abs((bb_l[2] - bb_l[0]) - (bb_r[2] - bb_r[0])) < 0.1
        assert abs((bb_l[3] - bb_l[1]) - (bb_r[3] - bb_r[1])) < 0.1

    def test_all_main_cross_members_same_bounding_box_size(self):
        """The 5 main cross members (not hyp_cross, which is rotated) have same bbox dims."""
        main_ids = [k for k in EXPECTED_IDS if "cross" in k and k != "hyp_cross"]
        bbs = [self.by_id[cid]["bbox"] for cid in main_ids]
        for bb in bbs[1:]:
            assert abs((bb[2] - bb[0]) - (bbs[0][2] - bbs[0][0])) < 0.1
            assert abs((bb[3] - bb[1]) - (bbs[0][3] - bbs[0][1])) < 0.1

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

    def test_triangle_bbox_correct(self):
        """stand_L bounding box is STAND_BASE_L × STAND_UPRIGHT_H."""
        bb = self.by_id["stand_L"]["bbox"]
        assert abs((bb[2] - bb[0]) - p["STAND_BASE_L"]) < 0.1
        assert abs((bb[3] - bb[1]) - p["STAND_UPRIGHT_H"]) < 0.1

    def test_cross_bbox_correct(self):
        """Main cross members: (STAND_SPREAD_L+2*TEN_L) × STAND_SPREAD_W. hyp_cross is rotated."""
        total_l = p["STAND_SPREAD_L"] + 2.0 * p["STAND_SPREAD_TEN_L"]
        sw = p["STAND_SPREAD_W"]
        for cid in [k for k in EXPECTED_IDS if "cross" in k and k != "hyp_cross"]:
            bb = self.by_id[cid]["bbox"]
            assert abs((bb[2] - bb[0]) - total_l) < 0.1, f"{cid} w={bb[2]-bb[0]:.2f}"
            assert abs((bb[3] - bb[1]) - sw) < 0.1, f"{cid} h={bb[3]-bb[1]:.2f}"
        # hyp_cross placed rotated 90° on sheet: bbox is SW × total_l
        bb = self.by_id["hyp_cross"]["bbox"]
        assert abs((bb[2] - bb[0]) - sw) < 0.1, \
            f"hyp_cross width={bb[2]-bb[0]:.2f} != STAND_SPREAD_W={sw}"
        assert abs((bb[3] - bb[1]) - total_l) < 0.1, \
            f"hyp_cross height={bb[3]-bb[1]:.2f} != total_l={total_l}"


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

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "optional_loom_stand.svg")
            result = write(p, path=path)
            assert result == path
            assert os.path.exists(path)
            assert os.path.getsize(path) > 200
