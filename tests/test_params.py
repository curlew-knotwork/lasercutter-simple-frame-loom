"""
Tests for src/params.py — default parameter set.

Stage discipline: these tests are written BEFORE params.py exists.
All tests will FAIL until params.py is implemented correctly.

Each test:
  1. Calls the corresponding invariant predicate with the default params dict.
  2. Asserts the invariant holds.
  3. States what value it checked and why.

Unhappy-path tests verify that deliberately broken params trigger the right failures.
"""

import math
import sys
import os

import pytest

# Ensure src/ and proofs/ are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from proofs.invariants import (
    inv_tab_narrower_than_stile,
    inv_tab_wider_than_mat,
    inv_socket_wider_than_tab,
    inv_clearance_in_range,
    inv_notch_count_pitch_span,
    inv_notch_positions_within_rail,
    inv_notch_depth_less_than_rail,
    inv_no_mortise_3d_intersection,
    inv_crossbar_mortises_clear_corner_zone,
    inv_box_interior_holds_loom,
    inv_critical_parts_fit_sheet,
    inv_crossbar_geometry,
    inv_stand_notch_geometry,
    assert_all,
    check_all,
)


# ---------------------------------------------------------------------------
# Fixture: default params from src/params.py
# ---------------------------------------------------------------------------

@pytest.fixture
def p():
    from src.params import DEFAULT
    return DEFAULT


# ---------------------------------------------------------------------------
# Happy-path tests (default params must pass every invariant)
# ---------------------------------------------------------------------------

class TestDefaultParams:

    def test_tab_narrower_than_stile(self, p):
        ok, trace = inv_tab_narrower_than_stile(p)
        assert ok, trace

    def test_tab_wider_than_mat(self, p):
        """N=1 gives TAB_W=7.333mm > MAT=6mm. N=2 would give 4.4mm < 6mm (D-01)."""
        ok, trace = inv_tab_wider_than_mat(p)
        assert ok, trace

    def test_tab_width_exact_value(self, p):
        """TAB_W must equal STILE_W / 3 for N=1."""
        expected = p["STILE_W"] / 3.0
        assert abs(p["TAB_W"] - expected) < 1e-9, (
            f"TAB_W={p['TAB_W']:.6f} != STILE_W/3={expected:.6f}"
        )

    def test_socket_wider_than_tab(self, p):
        ok, trace = inv_socket_wider_than_tab(p)
        assert ok, trace

    def test_clearance_in_range(self, p):
        ok, trace = inv_clearance_in_range(p)
        assert ok, trace

    def test_clearance_exact_value(self, p):
        """Finger joint clearance must be 0.05–0.40mm. (D-13: no crossbar tenon, no tenon clearance.)"""
        fc = p["SOCK_W"] - p["TAB_W"]
        assert 0.05 <= fc <= 0.40, f"finger clearance={fc:.4f}mm out of range"

    def test_notch_count_pitch_span(self, p):
        """(31-1)*10 = 300 = INTERIOR_W. DEF-001 was (20-1)*10 = 190 ≠ 200."""
        ok, trace = inv_notch_count_pitch_span(p)
        assert ok, trace

    def test_notch_count_is_31(self, p):
        assert p["NOTCH_COUNT"] == 31, f"NOTCH_COUNT={p['NOTCH_COUNT']}, expected 31"

    def test_notch_pitch_is_10(self, p):
        assert abs(p["NOTCH_PITCH"] - 10.0) < 1e-9

    def test_notch_positions_within_rail(self, p):
        ok, trace = inv_notch_positions_within_rail(p)
        assert ok, trace

    def test_notch_start_at_inner_stile_face(self, p):
        """First notch centreline must be at STILE_W from rail outer edge."""
        assert abs(p["NOTCH_START_X"] - p["STILE_W"]) < 1e-9, (
            f"NOTCH_START_X={p['NOTCH_START_X']:.4f} != STILE_W={p['STILE_W']:.4f}"
        )

    def test_notch_end_at_opposite_inner_stile_face(self, p):
        """Last notch centreline must be at STILE_W + INTERIOR_W from rail outer edge."""
        expected = p["STILE_W"] + p["INTERIOR_W"]
        assert abs(p["NOTCH_END_X"] - expected) < 1e-9, (
            f"NOTCH_END_X={p['NOTCH_END_X']:.4f} != {expected:.4f}"
        )

    def test_notch_depth_less_than_rail(self, p):
        ok, trace = inv_notch_depth_less_than_rail(p)
        assert ok, trace

    def test_no_mortise_3d_intersection(self, p):
        """D-08 eliminated prop mortises; only same-face crossbar mortises remain."""
        ok, trace = inv_no_mortise_3d_intersection(p)
        assert ok, trace

    def test_crossbar_mortise_positions_distinct(self, p):
        """CROSS1 and CROSS2 must be at different heights (not the same slot)."""
        separation = abs(p["CROSS2_CENTRE"] - p["CROSS1_CENTRE"])
        min_separation = p["CROSS_MORT_W"]  # at minimum must not overlap
        assert separation > min_separation, (
            f"Crossbar centres too close: separation={separation:.2f}mm, "
            f"min={min_separation:.2f}mm"
        )

    def test_crossbar_mortises_clear_corner_zone(self, p):
        ok, trace = inv_crossbar_mortises_clear_corner_zone(p)
        assert ok, trace

    def test_crossbar_geometry(self, p):
        ok, trace = inv_crossbar_geometry(p)
        assert ok, trace

    def test_crossbar1_at_one_third_interior(self, p):
        """CROSS1 centre = RAIL_W + INTERIOR_H/3."""
        expected = p["RAIL_W"] + p["INTERIOR_H"] / 3.0
        assert abs(p["CROSS1_CENTRE"] - expected) < 0.5, (
            f"CROSS1_CENTRE={p['CROSS1_CENTRE']:.2f}, expected≈{expected:.2f}"
        )

    def test_crossbar2_at_two_thirds_interior(self, p):
        """CROSS2 centre = RAIL_W + 2*INTERIOR_H/3."""
        expected = p["RAIL_W"] + 2.0 * p["INTERIOR_H"] / 3.0
        assert abs(p["CROSS2_CENTRE"] - expected) < 0.5, (
            f"CROSS2_CENTRE={p['CROSS2_CENTRE']:.2f}, expected≈{expected:.2f}"
        )

    def test_stile_body_height(self, p):
        expected = p["INTERIOR_H"] + 2 * p["RAIL_W"]
        assert abs(p["STILE_BODY_H"] - expected) < 1e-9

    def test_stile_total_height(self, p):
        expected = p["STILE_BODY_H"] + 2 * p["MAT"]
        assert abs(p["STILE_TOTAL_H"] - expected) < 1e-9

    def test_frame_outer_width(self, p):
        expected = p["INTERIOR_W"] + 2 * p["STILE_W"]
        assert abs(p["FRAME_OUTER_W"] - expected) < 1e-9

    def test_frame_outer_height(self, p):
        expected = p["INTERIOR_H"] + 2 * p["RAIL_W"]
        assert abs(p["FRAME_OUTER_H"] - expected) < 1e-9

    def test_stand_notch_geometry(self, p):
        ok, trace = inv_stand_notch_geometry(p)
        assert ok, trace

    def test_box_interior_holds_loom(self, p):
        ok, trace = inv_box_interior_holds_loom(p)
        assert ok, trace

    def test_critical_parts_fit_sheet(self, p):
        ok, trace = inv_critical_parts_fit_sheet(p)
        assert ok, trace

    def test_stile_fits_in_600mm_sheet(self, p):
        """Stile total height 456mm + 2*2mm margin = 460mm <= 600mm."""
        assert p["STILE_TOTAL_H"] + 2 * p["MARGIN"] <= p["SHEET_H"], (
            f"Stile {p['STILE_TOTAL_H']}mm + margins doesn't fit in {p['SHEET_H']}mm sheet"
        )

    def test_assert_all_passes(self, p):
        """Catch-all: assert_all() must not raise for default params."""
        assert_all(p)  # raises AssertionError if any invariant fails

    def test_beater_tooth_pitch_matches_notch_pitch(self, p):
        """Beater tooth pitch must equal warp notch pitch for alignment."""
        assert abs(p["BEATER_TOOTH_PITCH"] - p["NOTCH_PITCH"]) < 1e-9, (
            f"beater pitch {p['BEATER_TOOTH_PITCH']} != notch pitch {p['NOTCH_PITCH']}"
        )

    def test_beater_tooth_count_matches_notch_count(self, p):
        assert p["BEATER_TOOTH_COUNT"] == p["NOTCH_COUNT"], (
            f"beater teeth {p['BEATER_TOOTH_COUNT']} != notches {p['NOTCH_COUNT']}"
        )

    def test_crossbar_body_width_equals_interior_w(self, p):
        assert abs(p["CROSS_BODY_W"] - p["INTERIOR_W"]) < 1e-9

    def test_heddle_holes_clear_of_corner_socket_zone(self, p):
        """Heddle holes in top rail must not overlap with finger socket zones at rail ends."""
        socket_zone_end = p["MAT"]  # socket zone: 0 to MAT from each rail end
        left_hole_x = p["HEDDLE_HOLE_1_X"]
        right_hole_x = p["HEDDLE_HOLE_2_X"]
        r = p["HEDDLE_HOLE_R"]
        # Left hole: nearest edge of hole must be > socket zone
        assert left_hole_x - r > socket_zone_end, (
            f"Left heddle hole edge at {left_hole_x - r:.2f} overlaps socket zone [0, {socket_zone_end}]"
        )
        # Right hole: from right end of rail
        rail_w = p["FRAME_OUTER_W"]
        assert right_hole_x + r < rail_w - socket_zone_end, (
            f"Right heddle hole edge at {right_hole_x + r:.2f} overlaps socket zone"
        )


# ---------------------------------------------------------------------------
# Unhappy-path tests: broken params must fail the right invariants
# ---------------------------------------------------------------------------

def _mutate(base: dict, **overrides) -> dict:
    """Return a copy of base with overrides applied."""
    p = dict(base)
    p.update(overrides)
    return p


class TestUnhappyPath:

    def test_n2_tab_too_narrow(self, p):
        """N=2 gives TAB_W=22/5=4.4mm < MAT=6mm — must fail I-5."""
        bad = _mutate(p, TAB_W=p["STILE_W"] / 5.0)  # N=2
        ok, trace = inv_tab_wider_than_mat(bad)
        assert not ok, f"Expected I-5 to fail for N=2 tab, but got: {trace}"

    def test_zero_clearance_fails(self, p):
        """SOCK_W == TAB_W → clearance=0 < 0.05 — must fail I-7."""
        bad = _mutate(p, SOCK_W=p["TAB_W"], CROSS_MORT_W=p["CROSS_TEN_W"])
        ok, trace = inv_clearance_in_range(bad)
        assert not ok, f"Expected I-7 to fail for zero clearance: {trace}"

    def test_excessive_clearance_fails(self, p):
        """SOCK_W >> TAB_W → clearance > 0.40mm — must fail I-7."""
        bad = _mutate(p, SOCK_W=p["TAB_W"] + 1.0, CROSS_MORT_W=p["CROSS_TEN_W"] + 1.0)
        ok, trace = inv_clearance_in_range(bad)
        assert not ok, f"Expected I-7 to fail for excessive clearance: {trace}"

    def test_wrong_notch_count_fails(self, p):
        """20 notches with 10mm pitch over 300mm interior violates I-8."""
        bad = _mutate(p, NOTCH_COUNT=20)
        ok, trace = inv_notch_count_pitch_span(bad)
        assert not ok, f"Expected I-8 to fail for 20 notches: {trace}"

    def test_notch_too_deep_fails(self, p):
        """Notch depth >= RAIL_W cuts through rail — must fail I-9."""
        bad = _mutate(p, NOTCH_D=p["RAIL_W"])
        ok, trace = inv_notch_depth_less_than_rail(bad)
        assert not ok, f"Expected I-9 to fail for notch_depth==rail_w: {trace}"

    def test_overlapping_crossbar_mortises_fail(self, p):
        """Crossbars at same height — must fail I-3."""
        bad = _mutate(p, CROSS2_CENTRE=p["CROSS1_CENTRE"])  # same position
        ok, trace = inv_no_mortise_3d_intersection(bad)
        assert not ok, f"Expected I-3 to fail for overlapping crossbars: {trace}"

    def test_crossbar_in_corner_zone_fails(self, p):
        """Crossbar mortise entering corner tab zone — must fail I-11."""
        bad = _mutate(p, CROSS1_CENTRE=p["MAT"] / 2.0)  # inside corner zone
        ok, trace = inv_crossbar_mortises_clear_corner_zone(bad)
        assert not ok, f"Expected I-11 to fail for crossbar in corner zone: {trace}"

    def test_box_too_short_fails(self, p):
        """Box interior length shorter than stile — must fail I-10."""
        bad = _mutate(p, BOX_INTERIOR_L=p["STILE_TOTAL_H"] - 10.0)
        ok, trace = inv_box_interior_holds_loom(bad)
        assert not ok, f"Expected I-10 to fail for box too short: {trace}"

    def test_stile_too_tall_for_sheet_fails(self, p):
        """Interior height so large that stile exceeds sheet — must fail I-1-partial."""
        bad = _mutate(p,
            INTERIOR_H=580.0,
            STILE_BODY_H=580.0 + 2 * p["RAIL_W"],
            STILE_TOTAL_H=580.0 + 2 * p["RAIL_W"] + 2 * p["MAT"],
            FRAME_OUTER_H=580.0 + 2 * p["RAIL_W"],
        )
        ok, trace = inv_critical_parts_fit_sheet(bad)
        assert not ok, f"Expected I-1-partial to fail for oversized stile: {trace}"

    def test_stand_notch_too_narrow_fails(self, p):
        """Notch narrower than stile — must fail I-5c."""
        bad = _mutate(p, STAND_NOTCH_W=p["STILE_W"] - 1.0)
        ok, trace = inv_stand_notch_geometry(bad)
        assert not ok, f"Expected I-5c to fail for narrow notch: {trace}"

    def test_stand_notch_too_wide_fails(self, p):
        """Notch much wider than stile — loom wobbles — must fail I-5c."""
        bad = _mutate(p, STAND_NOTCH_W=p["STILE_W"] + 5.0)
        ok, trace = inv_stand_notch_geometry(bad)
        assert not ok, f"Expected I-5c to fail for loose notch: {trace}"
