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
    notch_pitch: float = 5.0,    # mm, warp notch centre-to-centre pitch (D-29)
    mat: float = 6.0,            # mm, loom material (nominal)
    mat3: float = 3.0,           # mm, box/stand material (nominal)
    sheet_w: float = 600.0,      # mm, sheet width
    sheet_h: float = 600.0,      # mm, sheet height
    kerf: float = 0.15,          # mm per cut side
    margin: float = 2.0,         # mm, min clearance part-to-edge and part-to-part
) -> dict:
    """
    Derive all parameters from base values.
    Raises ValueError for out-of-range primary knobs (D-29).
    Raises AssertionError if any geometric invariant is violated.
    """

    # ------------------------------------------------------------------
    # Input validation (D-29)
    # ------------------------------------------------------------------
    if not (150.0 <= interior_w <= 500.0):
        raise ValueError(f"interior_w={interior_w} outside [150, 500]mm (D-29)")
    if not (200.0 <= interior_h <= 550.0):
        raise ValueError(f"interior_h={interior_h} outside [200, 550]mm (D-29)")
    if not (4.0 <= notch_pitch <= 15.0):
        raise ValueError(f"notch_pitch={notch_pitch} outside [4, 15]mm (D-29)")
    if abs(round(interior_w / notch_pitch) * notch_pitch - interior_w) > 0.001:
        raise ValueError(
            f"interior_w={interior_w} not divisible by notch_pitch={notch_pitch} "
            f"(D-29: (notch_count-1)×pitch must equal interior_w)"
        )

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
    # Warp notches (D-06, D-24, D-29)
    # (count-1) * pitch == interior_w  →  count = interior_w/pitch + 1
    # Must be an integer. For pitch=5, interior_w=300: count=61 ✓ (D-24)
    # notch_pitch is now a primary knob (D-29); validated above.
    # ------------------------------------------------------------------
    notch_count = int(round(interior_w / notch_pitch)) + 1
    notch_w     = notch_pitch * 0.4   # 40% notch, 60% tooth (D-29)
    notch_d     = 5.0                 # mm notch depth
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
    shuttle_w       = 28.0
    shuttle_taper_l = 22.0
    shuttle_notch_hw = 5.0 * 4.0 / 3.0  # V-notch half-width at tip (D-26: was 5mm; +1/3 larger)
    # D-29: shuttle_l and shuttle_light_l auto-derived from interior_w
    shuttle_l       = round(max(120.0, min(interior_w * 0.6, 280.0)) / 5.0) * 5.0
    shuttle_light_l = max(shuttle_l - 2.0 * shuttle_taper_l - 10.0, 20.0)
    shuttle_light_w = 12.0   # lightening ellipse semi-minor axis × 2

    # ------------------------------------------------------------------
    # Beater / comb
    # Spans interior_w + 10mm overhang (5mm each side)
    # Teeth align with warp notches: same pitch, same count
    # ------------------------------------------------------------------
    beater_overhang   = 5.0   # mm each side past inner stile face
    beater_w          = interior_w + 2.0 * beater_overhang
    beater_handle_h   = 22.0
    beater_tooth_w    = notch_w                          # D-29: matches notch_w at any pitch
    beater_tooth_h    = min(notch_w * 10.0, 20.0)       # D-29, D-33: 20mm at default pitch=5
    beater_total_h    = beater_handle_h + beater_tooth_h
    beater_tooth_gap  = notch_pitch - beater_tooth_w   # = 3.0mm at 5mm pitch
    beater_tooth_pitch = beater_tooth_w + beater_tooth_gap  # = notch_pitch
    beater_tooth_count = notch_count - 1               # D-30: one tooth per inter-warp gap
    beater_grip_count = 3
    beater_grip_rx    = 8.0  # mm ellipse semi-major
    beater_grip_ry    = 3.5  # mm ellipse semi-minor

    # ------------------------------------------------------------------
    # Heddle bar (laser-cut flat bar resting across frame top)
    # ------------------------------------------------------------------
    heddle_bar_l     = frame_outer_w - 2.0 * stile_w + 2.0 * 12.0  # 24mm past each inner face
    heddle_bar_w     = 20.0
    heddle_bar_hole_r = 1.5  # mm semicircle radius (D-24: was 3.5mm; width=3mm, 2mm gap at 5mm pitch)
    heddle_bar_hole_h = 6.0  # mm total hole height (was 8mm; shortened to preserve material between holes)
    heddle_bar_hole_pitch = notch_pitch
    heddle_bar_hole_count = notch_count
    heddle_bar_slot_w = 2.0 * heddle_bar_hole_r  # = 3.0mm — rect slot width (D-32)
    heddle_bar_slot_h = 12.0                     # mm — rect slot height; 4mm material margin each side (D-32)
    heddle_bar_corner_r = 2.0  # mm — outer corner fillet (hand-held moving part)

    corner_r = 0.5  # mm — fillet radius on rail notch and beater tooth corners (D-25)

    # ------------------------------------------------------------------
    # Stand (D-23) — 6mm ply, optional separate sheet, 2-piece triangular X easel
    # Two identical right-triangle pieces, cross-halving half-lap joint at centre.
    # Piece B is piece A flipped horizontally for assembly.
    # Foot tab (convex, +bump) captures loom bottom rail. No rail notch.
    # ------------------------------------------------------------------
    stand_rail_tab_l  = 0.0            # D-18 legacy: no top-rail tabs; top rail = FRAME_OUTER_W
    stand_x_l         = frame_outer_h  # D-29: piece length = frame outer height
    stand_x_w         = 120.0   # mm foot width (wide end of triangle; D-31: 15° lean)
    stand_x_slot_w    = mat + 0.1               # = 6.1mm cross-halving slot width (clearance fit)
    # At slot_cx = L/2, triangle height = W/2. Slot depth = half that = W/4.
    stand_x_slot_d    = stand_x_w / 4.0         # = 20.0mm slot depth (cross-halving at triangle mid)
    stand_x_tab_l     = 30.0    # mm foot tab protrusion length (+y from hyp at foot); RAIL_W(22)+8mm clearance
    stand_x_tab_h     = 20.0    # mm foot tab height (bottom zone of foot edge, y=W−TAB_H..W)
    stand_x_bump_l    = 5.0     # mm bump length at outer tab end (mechanical stop)
    stand_x_bump_h    = 5.0     # mm bump height at outer tab end (prevents rail sliding off)
    stand_x_tip_w     = 10.0   # mm flat blunt-end width at triangle tip (D-28; = 2×CORNER_R → semicircle)
    stand_x_corner_r  = 0.0    # mm outer corner fillet radius (D-28: tip squared off only; other corners straight)

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
    # Wall-to-base joint (D-15, updated D-20): tabs on wall bottom edges, edge notches in base
    box_base_ntabs_l = 15   # long wall (D-20)
    box_base_ntabs_s = 5    # short wall (D-20)

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
        "HEDDLE_BAR_HOLE_H":     heddle_bar_hole_h,
        "HEDDLE_BAR_HOLE_PITCH": heddle_bar_hole_pitch,
        "HEDDLE_BAR_HOLE_COUNT": heddle_bar_hole_count,
        "HEDDLE_BAR_SLOT_W":     heddle_bar_slot_w,
        "HEDDLE_BAR_SLOT_H":     heddle_bar_slot_h,
        "HEDDLE_BAR_CORNER_R":   heddle_bar_corner_r,
        "CORNER_R":              corner_r,

        # Stand (6mm ply, D-23 — optional separate sheet, 2-piece triangular X easel)
        "STAND_RAIL_TAB_L":         stand_rail_tab_l,
        "STAND_X_L":                stand_x_l,
        "STAND_X_W":                stand_x_w,
        "STAND_X_SLOT_W":           stand_x_slot_w,
        "STAND_X_SLOT_D":           stand_x_slot_d,
        "STAND_X_TAB_L":            stand_x_tab_l,
        "STAND_X_TAB_H":            stand_x_tab_h,
        "STAND_X_BUMP_L":           stand_x_bump_l,
        "STAND_X_BUMP_H":           stand_x_bump_h,
        "STAND_X_TIP_W":            stand_x_tip_w,
        "STAND_X_CORNER_R":         stand_x_corner_r,

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
