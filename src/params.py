"""
src/params.py — All design constants for the frame loom.

Single source of truth. Every number in every generator imports from here.
No generator or SVG file contains hardcoded dimensions.

Usage:
    from src.params import DEFAULT   # default 300×400mm loom
    from src.params import make_params  # parametric: make_params(interior_w=250, interior_h=350)

At import: assert_all(DEFAULT) is called. If any invariant fails, import raises AssertionError.
No SVG is ever written for an invalid parameter set.

Reference: DECISIONS.md D-12, ARCHITECTURE.md § src/params.py
"""

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from proofs.invariants import assert_all


def make_params(
    interior_w: float = 300.0,   # mm, weaving interior width
    interior_h: float = 400.0,   # mm, weaving interior height
    mat: float = 6.0,            # mm, loom material (nominal)
    mat3: float = 3.0,           # mm, box/stand material (nominal)
    sheet_w: float = 600.0,      # mm, sheet width
    sheet_h: float = 600.0,      # mm, sheet height
    kerf: float = 0.15,          # mm per cut side
    margin: float = 2.0,         # mm, min clearance part-to-edge and part-to-part
) -> dict:
    """
    Derive all parameters from base values.
    Raises AssertionError if any geometric invariant is violated.
    """

    # ------------------------------------------------------------------
    # Structural member widths (fixed by finger-joint analysis, D-01)
    # N=1 tab per corner → tab_w = stile_w/3 must be > mat
    # Solving: stile_w/3 > mat → stile_w > 3*mat = 18mm.
    # Chosen: stile_w = 22mm (gives 7.33mm tab, 22% margin over mat=6mm).
    # ------------------------------------------------------------------
    stile_w = 22.0   # mm — also used as rail width (equal → uniform finger pitch)
    rail_w  = stile_w

    # ------------------------------------------------------------------
    # Frame outer dimensions
    # ------------------------------------------------------------------
    frame_outer_w = interior_w + 2.0 * stile_w
    frame_outer_h = interior_h + 2.0 * rail_w
    stile_body_h  = frame_outer_h                        # stile body spans full outer height
    stile_total_h = stile_body_h + 2.0 * mat             # + tab protrusions each end

    # ------------------------------------------------------------------
    # Finger joints — corner tabs (D-01, D-04)
    # N=1: one central tab per corner joint
    # tab_w = stile_w / (2*1+1) = stile_w / 3
    # sock_w = tab_w + joint_clearance
    # ------------------------------------------------------------------
    n_fingers        = 1
    tab_w            = stile_w / (2.0 * n_fingers + 1.0)   # = 7.3333mm
    joint_clearance  = 0.10                                  # mm, socket - tab
    sock_w           = tab_w + joint_clearance               # = 7.4333mm
    tab_l            = mat                                    # finger tab length = mat thickness

    # ------------------------------------------------------------------
    # Warp notches (D-06)
    # (count-1) * pitch == interior_w  →  count = interior_w/pitch + 1
    # Must be an integer. For pitch=10, interior_w=300: count=31 ✓
    # ------------------------------------------------------------------
    notch_pitch = 10.0    # mm centre-to-centre
    notch_count = int(round(interior_w / notch_pitch)) + 1
    notch_w     = 4.0     # mm notch opening width (U-bottom, D-02)
    notch_d     = 5.0     # mm notch depth
    notch_start_x = stile_w                              # first centreline from rail outer edge
    notch_end_x   = stile_w + (notch_count - 1) * notch_pitch  # = stile_w + interior_w

    # ------------------------------------------------------------------
    # Crossbars — structural anti-bow (D-13, supersedes D-07)
    # Two crossbars at 1/3 and 2/3 of interior height (rounded to nearest 0.5mm)
    # No tenons: body = INTERIOR_W exactly. Mortise = closed rect_hole in stile.
    # CROSS_H = 20mm (37× stiffer than 6mm in bending). Assembled before rails.
    # ------------------------------------------------------------------
    cross_h       = 20.0               # mm crossbar height (D-13; was MAT=6mm)
    cross_body_w  = interior_w          # spans between stile inner faces
    cross_ten_l   = 0.0                # no tenon (D-13)
    cross_total_l = cross_body_w       # = INTERIOR_W (no tenons)
    cross_ten_w   = 0.0                # no tenon (D-13)
    # Mortise = registration pocket on stile inner face: 5mm deep × (CROSS_H+0.1) tall
    cross_mort_d  = 5.0                # mm pocket depth from inner face
    cross_mort_w  = cross_h + 0.10     # = 20.1mm (fits crossbar height + clearance)

    # Mortise centres from stile top (rounded to nearest 0.5mm for clean SVG coords)
    cross1_centre = round((rail_w + interior_h / 3.0) * 2.0) / 2.0
    cross2_centre = round((rail_w + 2.0 * interior_h / 3.0) * 2.0) / 2.0

    # ------------------------------------------------------------------
    # Heddle holes in top rail (two holes for heddle bar to rest across)
    # ------------------------------------------------------------------
    heddle_hole_r   = 4.0    # mm radius (= 8mm diameter hole)
    heddle_hole_1_x = stile_w + 14.0                    # 14mm from inner stile face
    heddle_hole_2_x = frame_outer_w - stile_w - 14.0    # symmetric on right side

    # ------------------------------------------------------------------
    # Shuttle (D-06 accessories)
    # ------------------------------------------------------------------
    shuttle_l       = 180.0
    shuttle_w       = 28.0
    shuttle_taper_l = 22.0
    shuttle_notch_hw = 5.0   # V-notch half-width at tip
    shuttle_light_l = 110.0  # lightening ellipse semi-major axis × 2
    shuttle_light_w = 12.0   # lightening ellipse semi-minor axis × 2

    # ------------------------------------------------------------------
    # Beater / comb
    # Spans interior_w + 10mm overhang (5mm each side)
    # Teeth align with warp notches: same pitch, same count
    # ------------------------------------------------------------------
    beater_overhang   = 5.0   # mm each side past inner stile face
    beater_w          = interior_w + 2.0 * beater_overhang
    beater_handle_h   = 22.0
    beater_tooth_h    = 20.0
    beater_total_h    = beater_handle_h + beater_tooth_h
    beater_tooth_w    = 4.0
    beater_tooth_gap  = notch_pitch - beater_tooth_w   # = 6.0mm at 10mm pitch
    beater_tooth_pitch = beater_tooth_w + beater_tooth_gap  # = notch_pitch
    beater_tooth_count = notch_count                    # matches warp count
    beater_grip_count = 3
    beater_grip_rx    = 8.0  # mm ellipse semi-major
    beater_grip_ry    = 3.5  # mm ellipse semi-minor

    # ------------------------------------------------------------------
    # Heddle bar (laser-cut flat bar resting across frame top)
    # ------------------------------------------------------------------
    heddle_bar_l     = frame_outer_w - 2.0 * stile_w + 2.0 * 12.0  # 24mm past each inner face
    heddle_bar_w     = 20.0
    heddle_bar_hole_r = 3.5  # mm
    heddle_bar_hole_pitch = notch_pitch
    heddle_bar_hole_count = notch_count
    heddle_bar_offset = 2.5  # mm — alternating hole stagger for rigid heddle two-shed (D-17 answer)

    # ------------------------------------------------------------------
    # Triangle stand (D-18 + D-19) — 6mm ply, optional separate sheet
    # Two solid right-triangle side pieces + 6 cross members (3 rear, 2 base, 1 hyp).
    # ------------------------------------------------------------------
    stand_upright_h   = 420.0    # mm triangle upright height (rear/left edge)
    stand_base_l      = 240.0    # mm triangle base length (bottom edge)
    stand_rail_tab_l  = 0.0      # D-18: no top-rail tabs; top rail = FRAME_OUTER_W
    # Edge notch in triangle for cross member (30mm wide × 15mm deep)
    stand_spread_l    = frame_outer_w   # = 344mm cross member body span
    stand_spread_w    = 30.0            # mm cross member height (stands on edge)
    stand_spread_ten_l = 15.0           # mm each end sits in edge notch
    stand_notch_w     = stand_spread_w + 0.1   # = 30.1mm notch height (fits cross member + 0.1 clearance)
    stand_notch_d     = 15.0                   # mm edge notch depth
    stand_spread_mort_w = stand_notch_w        # = 30.1mm (same as notch width)
    stand_spread_mort_d = stand_notch_d        # = 15mm (same as notch depth)
    # D-19: L-shaped drop-Z entry on upright edge notches
    stand_notch_entry   = 2.0   # mm extra height above captive zone (wide entry allows 2mm vertical play)
    stand_notch_entry_d = 8.0   # mm partial depth of entry zone (step at x=8 forces 2mm drop before x=15)
    # Upright edge notch y-centres from top (rear cross member positions)
    stand_mort_y_top  = 60.0    # mm — upper rear cross centre from upright top
    stand_mort_y_mid  = 210.0   # mm — middle rear cross centre from upright top
    stand_mort_y_bot  = 360.0   # mm — lower rear cross centre from upright top
    # Base edge notch x-centres from back end (base cross member positions)
    stand_base_notch_x1 = 80.0  # mm — base cross 1 centre from back of base
    stand_base_notch_x2 = 160.0 # mm — base cross 2 centre from back of base
    # Stile slots in rear cross members 1 and 3 (loom stile drop-in)
    stand_stile_slot_w = stile_w + 0.5   # = 22.5mm (STILE_W + 0.5mm clearance each side)
    stand_stile_slot_d = 15.0            # mm slot depth from loom-facing edge
    # D-19: hypotenuse cross member — notch on hyp edge at t=0.25 from top vertex
    stand_hyp_t  = 0.25
    stand_hyp_cx = stand_hyp_t * stand_base_l      # = 60.0mm from upright (back)
    stand_hyp_cy = stand_hyp_t * stand_upright_h   # = 105.0mm from top

    # ------------------------------------------------------------------
    # Box (D-09) — 3mm ply, holds all loom parts flat in a single layer
    # ------------------------------------------------------------------
    # Longest part: stile_total_h
    # Parts laid flat; pack_w is the total width when all parts are laid side by side
    # Estimate (refined in box.py / verify_box.py):
    pack_w_estimate = (
        2.0 * stile_w        # 2 stiles
        + 2.0 * rail_w       # 2 rails (same width as stile)
        + 2.0 * cross_h      # 2 crossbars (h=20mm face-up in box)
        + 2.0 * shuttle_w    # 2 shuttles
        + beater_total_h     # beater
        + heddle_bar_w       # heddle bar
        + 4.0 * margin       # inter-part gaps
    )

    box_interior_l = math.ceil(stile_total_h + 4.0)  # stile + 4mm clearance, round up
    box_interior_w = math.ceil(pack_w_estimate + 4.0)
    box_interior_h = 12.0          # D-14: 12mm (2×MAT3 tabs, comfortable flat-layer clearance)

    box_wall_t    = mat3
    box_outer_l   = box_interior_l + 2.0 * box_wall_t
    box_outer_w   = box_interior_w + 2.0 * box_wall_t
    box_dado_d    = 2.0             # mm dado groove depth (unused — slot is at wall top)
    box_dado_w    = mat3 + 0.2      # mm lid slot depth in short walls (lid slides through)
    box_lid_clear = 0.1             # mm clearance each side of lid
    box_tab_w     = box_interior_h / 3.0  # mm N=1 finger joint tab: 12/3 = 4mm (D-15)
    # Wall-to-base joint (D-15): tabs on wall bottom edges, edge notches in base
    # 1 tab per ~22mm, minimum 8 (sparring round 2 answer)
    box_base_ntabs_l = max(8, round(box_outer_l / 22.0))
    box_base_ntabs_s = max(8, round(box_interior_w / 22.0))

    # ------------------------------------------------------------------
    # Assemble params dict
    # ------------------------------------------------------------------
    p = {
        # Base
        "INTERIOR_W":   interior_w,
        "INTERIOR_H":   interior_h,
        "MAT":          mat,
        "MAT3":         mat3,
        "SHEET_W":      sheet_w,
        "SHEET_H":      sheet_h,
        "KERF":         kerf,
        "MARGIN":       margin,

        # Frame
        "STILE_W":        stile_w,
        "RAIL_W":         rail_w,
        "FRAME_OUTER_W":  frame_outer_w,
        "FRAME_OUTER_H":  frame_outer_h,
        "STILE_BODY_H":   stile_body_h,
        "STILE_TOTAL_H":  stile_total_h,

        # Finger joints
        "N_FINGERS":       n_fingers,
        "TAB_W":           tab_w,
        "TAB_L":           tab_l,
        "JOINT_CLEARANCE": joint_clearance,
        "SOCK_W":          sock_w,

        # Warp notches
        "NOTCH_COUNT":   notch_count,
        "NOTCH_PITCH":   notch_pitch,
        "NOTCH_W":       notch_w,
        "NOTCH_D":       notch_d,
        "NOTCH_START_X": notch_start_x,
        "NOTCH_END_X":   notch_end_x,

        # Crossbars
        "CROSS_BODY_W":   cross_body_w,
        "CROSS_TEN_L":    cross_ten_l,
        "CROSS_TOTAL_L":  cross_total_l,
        "CROSS_H":        cross_h,
        "CROSS_TEN_W":    cross_ten_w,
        "CROSS_MORT_D":   cross_mort_d,
        "CROSS_MORT_W":   cross_mort_w,
        "CROSS1_CENTRE":  cross1_centre,
        "CROSS2_CENTRE":  cross2_centre,

        # Heddle holes
        "HEDDLE_HOLE_R":   heddle_hole_r,
        "HEDDLE_HOLE_1_X": heddle_hole_1_x,
        "HEDDLE_HOLE_2_X": heddle_hole_2_x,

        # Shuttle
        "SHUTTLE_L":        shuttle_l,
        "SHUTTLE_W":        shuttle_w,
        "SHUTTLE_TAPER_L":  shuttle_taper_l,
        "SHUTTLE_NOTCH_HW": shuttle_notch_hw,
        "SHUTTLE_LIGHT_L":  shuttle_light_l,
        "SHUTTLE_LIGHT_W":  shuttle_light_w,

        # Beater
        "BEATER_OVERHANG":     beater_overhang,
        "BEATER_W":            beater_w,
        "BEATER_HANDLE_H":     beater_handle_h,
        "BEATER_TOOTH_H":      beater_tooth_h,
        "BEATER_TOTAL_H":      beater_total_h,
        "BEATER_TOOTH_W":      beater_tooth_w,
        "BEATER_TOOTH_GAP":    beater_tooth_gap,
        "BEATER_TOOTH_PITCH":  beater_tooth_pitch,
        "BEATER_TOOTH_COUNT":  beater_tooth_count,
        "BEATER_GRIP_COUNT":   beater_grip_count,
        "BEATER_GRIP_RX":      beater_grip_rx,
        "BEATER_GRIP_RY":      beater_grip_ry,

        # Heddle bar
        "HEDDLE_BAR_L":          heddle_bar_l,
        "HEDDLE_BAR_W":          heddle_bar_w,
        "HEDDLE_BAR_HOLE_R":     heddle_bar_hole_r,
        "HEDDLE_BAR_HOLE_PITCH": heddle_bar_hole_pitch,
        "HEDDLE_BAR_HOLE_COUNT": heddle_bar_hole_count,
        "HEDDLE_BAR_OFFSET":     heddle_bar_offset,

        # Stand (6mm ply, D-18 — optional separate sheet)
        "STAND_UPRIGHT_H":       stand_upright_h,
        "STAND_BASE_L":          stand_base_l,
        "STAND_RAIL_TAB_L":      stand_rail_tab_l,
        "STAND_NOTCH_W":         stand_notch_w,
        "STAND_NOTCH_D":         stand_notch_d,
        "STAND_SPREAD_L":        stand_spread_l,
        "STAND_SPREAD_W":        stand_spread_w,
        "STAND_SPREAD_TEN_L":    stand_spread_ten_l,
        "STAND_SPREAD_MORT_W":   stand_spread_mort_w,
        "STAND_SPREAD_MORT_D":   stand_spread_mort_d,
        "STAND_MORT_Y_TOP":      stand_mort_y_top,
        "STAND_MORT_Y_MID":      stand_mort_y_mid,
        "STAND_MORT_Y_BOT":      stand_mort_y_bot,
        "STAND_BASE_NOTCH_X1":   stand_base_notch_x1,
        "STAND_BASE_NOTCH_X2":   stand_base_notch_x2,
        "STAND_STILE_SLOT_W":    stand_stile_slot_w,
        "STAND_STILE_SLOT_D":    stand_stile_slot_d,
        "STAND_NOTCH_ENTRY":     stand_notch_entry,
        "STAND_NOTCH_ENTRY_D":   stand_notch_entry_d,
        "STAND_HYP_T":           stand_hyp_t,
        "STAND_HYP_CX":          stand_hyp_cx,
        "STAND_HYP_CY":          stand_hyp_cy,

        # Box (3mm ply)
        "BOX_PACK_W_ESTIMATE": pack_w_estimate,
        "BOX_INTERIOR_L":      box_interior_l,
        "BOX_INTERIOR_W":      box_interior_w,
        "BOX_INTERIOR_H":      box_interior_h,
        "BOX_WALL_T":          box_wall_t,
        "BOX_OUTER_L":         box_outer_l,
        "BOX_OUTER_W":         box_outer_w,
        "BOX_DADO_D":          box_dado_d,
        "BOX_DADO_W":          box_dado_w,
        "BOX_LID_CLEAR":       box_lid_clear,
        "BOX_TAB_W":           box_tab_w,
        "BOX_BASE_NTABS_L":    box_base_ntabs_l,
        "BOX_BASE_NTABS_S":    box_base_ntabs_s,
    }

    # Validate before returning — fail fast, no silent bad geometry
    assert_all(p)
    return p


# Module-level default — triggers assert_all at import time
DEFAULT = make_params()


if __name__ == "__main__":
    from proofs.invariants import print_report
    print(f"Default params computed. Interior: {DEFAULT['INTERIOR_W']}×{DEFAULT['INTERIOR_H']}mm")
    print(f"Frame outer: {DEFAULT['FRAME_OUTER_W']}×{DEFAULT['FRAME_OUTER_H']}mm")
    print(f"Stile total height: {DEFAULT['STILE_TOTAL_H']}mm")
    print(f"Notch count: {DEFAULT['NOTCH_COUNT']} × {DEFAULT['NOTCH_PITCH']}mm pitch")
    print(f"Crossbar centres: {DEFAULT['CROSS1_CENTRE']:.1f}mm, {DEFAULT['CROSS2_CENTRE']:.1f}mm from stile top")
    print(f"Box interior: {DEFAULT['BOX_INTERIOR_L']}×{DEFAULT['BOX_INTERIOR_W']}×{DEFAULT['BOX_INTERIOR_H']:.1f}mm")
    print()
    print_report(DEFAULT)
