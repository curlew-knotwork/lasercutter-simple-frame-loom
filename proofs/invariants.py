"""
Formal invariant predicates for the frame loom design.
Reference: DECISIONS.md § D-12 (invariants I-1 through I-12).

All functions are PURE: no I/O, no SVG parsing, no side effects.
Each takes a params dict `p` and returns (bool, str) where:
  bool — True iff the invariant holds
  str  — proof trace showing the computation (suitable for logging)

Call check_all(p) for a full scan.
Call assert_all(p) to raise AssertionError listing every failure.

Invariants I-1, I-2, I-12 require a rendered layout or parsed SVG;
they live in proofs/verify_loom.py and proofs/verify_box.py.
This module covers I-3 through I-11 plus additional structural checks.
"""

import math


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _overlap(a0: float, a1: float, b0: float, b1: float) -> bool:
    """True iff open intervals (a0,a1) and (b0,b1) overlap. Requires a0<a1, b0<b1."""
    return a0 < b1 and b0 < a1


def _pass(label: str, detail: str) -> tuple:
    return True, f"PASS  {label}: {detail}"


def _fail(label: str, detail: str) -> tuple:
    return False, f"FAIL  {label}: {detail}"


# ---------------------------------------------------------------------------
# I-4: tab_width < STILE_W
# ---------------------------------------------------------------------------

def inv_tab_narrower_than_stile(p: dict) -> tuple:
    """
    I-4: tab_width < STILE_W
    Ensures the finger tab is narrower than the stile — basic geometry sanity.
    Proof: TAB_W = STILE_W / (2*N+1) with N=1 → TAB_W = STILE_W/3 < STILE_W ✓ for all STILE_W > 0.
    """
    tw, sw = p["TAB_W"], p["STILE_W"]
    detail = f"TAB_W={tw:.4f} < STILE_W={sw:.4f}"
    return (_pass("I-4", detail) if tw < sw else _fail("I-4", detail))


# ---------------------------------------------------------------------------
# I-5: tab_width > MAT
# ---------------------------------------------------------------------------

def inv_tab_wider_than_mat(p: dict) -> tuple:
    """
    I-5: tab_width > MAT
    Ensures the finger tab is wider than the material thickness — required for structural
    integrity. A tab narrower than MAT would snap under shear load.
    Proof obligation: STILE_W / (2*N+1) > MAT.
    For STILE_W=22, MAT=6: N=1 → 22/3=7.33 > 6 ✓. N=2 → 22/5=4.4 < 6 ✗ (D-01 rationale).
    """
    tw, mat = p["TAB_W"], p["MAT"]
    detail = f"TAB_W={tw:.4f} > MAT={mat:.4f}"
    return (_pass("I-5", detail) if tw > mat else _fail("I-5", detail))


# ---------------------------------------------------------------------------
# I-6: SOCK_W > TAB_W
# ---------------------------------------------------------------------------

def inv_socket_wider_than_tab(p: dict) -> tuple:
    """
    I-6: SOCK_W > TAB_W
    Socket must be strictly wider than tab so the joint can close.
    """
    sw, tw = p["SOCK_W"], p["TAB_W"]
    detail = f"SOCK_W={sw:.4f} > TAB_W={tw:.4f}"
    return (_pass("I-6", detail) if sw > tw else _fail("I-6", detail))


# ---------------------------------------------------------------------------
# I-7: 0.05 ≤ clearance ≤ 0.40 mm
# ---------------------------------------------------------------------------

def inv_clearance_in_range(p: dict) -> tuple:
    """
    I-7: 0.05 ≤ (SOCK_W - TAB_W) ≤ 0.40 mm
    Clearance below 0.05mm: joint will not close by hand (too tight even after kerf).
    Clearance above 0.40mm: joint is sloppy; frame will rack under warp tension.
    Applies to ALL joint types: finger joints AND crossbar mortise-tenon.
    """
    # D-13: crossbar has no tenon — mortise clearance check not applicable.
    results = []
    ok_all = True
    for label, sock, tab in [
        ("finger_joint", p["SOCK_W"], p["TAB_W"]),
    ]:
        c = sock - tab
        ok = 0.05 <= c <= 0.40
        ok_all = ok_all and ok
        detail = f"{label}: clearance={c:.4f}mm in [0.05, 0.40]"
        results.append("PASS" if ok else f"FAIL {detail}")
    trace = "; ".join(results)
    return (True, f"PASS  I-7: {trace}") if ok_all else (False, f"FAIL  I-7: {trace}")


# ---------------------------------------------------------------------------
# I-8: (notch_count - 1) * pitch == INTERIOR_W
# ---------------------------------------------------------------------------

def inv_notch_count_pitch_span(p: dict) -> tuple:
    """
    I-8: (NOTCH_COUNT - 1) * NOTCH_PITCH == INTERIOR_W
    The warp notch array must span exactly the interior width.
    First notch centreline at STILE_W, last at STILE_W + INTERIOR_W.
    With NOTCH_COUNT notches and pitch p: span = (count-1)*p = INTERIOR_W.
    Defect DEF-001 (old spec: 20 notches, 10mm pitch, 200mm interior) violated this.
    Fix: 31 notches, 10mm pitch, 300mm interior → (31-1)*10 = 300 ✓.
    """
    count, pitch, interior = p["NOTCH_COUNT"], p["NOTCH_PITCH"], p["INTERIOR_W"]
    span = (count - 1) * pitch
    ok = abs(span - interior) < 1e-9
    detail = f"(NOTCH_COUNT-1)*PITCH = ({count}-1)*{pitch} = {span:.6f}, INTERIOR_W={interior:.6f}"
    return (_pass("I-8", detail) if ok else _fail("I-8", detail))


# ---------------------------------------------------------------------------
# I-8b: notch positions within rail
# ---------------------------------------------------------------------------

def inv_notch_positions_within_rail(p: dict) -> tuple:
    """
    I-8b: All notch centrelines fall within [STILE_W, STILE_W + INTERIOR_W].
    First centreline = STILE_W (flush with inner stile face).
    Last centreline = STILE_W + INTERIOR_W = STILE_W + (NOTCH_COUNT-1)*PITCH.
    """
    start = p["NOTCH_START_X"]
    end = p["NOTCH_END_X"]
    expected_start = p["STILE_W"]
    expected_end = p["STILE_W"] + p["INTERIOR_W"]
    ok = (abs(start - expected_start) < 1e-9) and (abs(end - expected_end) < 1e-9)
    detail = (f"start={start:.4f} (expected {expected_start:.4f}), "
              f"end={end:.4f} (expected {expected_end:.4f})")
    return (_pass("I-8b", detail) if ok else _fail("I-8b", detail))


# ---------------------------------------------------------------------------
# I-9: notch_depth < RAIL_W
# ---------------------------------------------------------------------------

def inv_notch_depth_less_than_rail(p: dict) -> tuple:
    """
    I-9: NOTCH_D < RAIL_W
    Notch must not cut through the rail. Material remaining = RAIL_W - NOTCH_D > 0.
    """
    nd, rw = p["NOTCH_D"], p["RAIL_W"]
    remaining = rw - nd
    ok = remaining > 0
    detail = f"NOTCH_D={nd:.4f}, RAIL_W={rw:.4f}, remaining={remaining:.4f}mm"
    return (_pass("I-9", detail) if ok else _fail("I-9", detail))


# ---------------------------------------------------------------------------
# I-3: No mortise 3D intersection
# ---------------------------------------------------------------------------

def inv_no_mortise_3d_intersection(p: dict) -> tuple:
    """
    I-3: No two mortises on the same member intersect in 3D.

    Two mortise slots intersect in 3D iff BOTH:
      (a) their height ranges overlap (they share a zone along the member's long axis), AND
      (b) they are on opposite faces AND their combined depth exceeds the member width.

    For same-face mortises: only (a) applies — they must not share height range
    (overlap would merge them into one undefined slot).

    Current design (D-08): stile has only two mortises, both on the INNER face:
      - CROSS1: inner face, depth=CROSS_MORT_D, centre at CROSS1_CENTRE from stile top
      - CROSS2: inner face, depth=CROSS_MORT_D, centre at CROSS2_CENTRE from stile top
    No prop mortises (D-08 eliminated them to avoid this exact failure class).
    No opposite-face mortise pairs exist.

    Same-face pair (CROSS1, CROSS2):
      Height ranges must not overlap.
    """
    half = p["CROSS_MORT_W"] / 2
    c1_top = p["CROSS1_CENTRE"] - half
    c1_bot = p["CROSS1_CENTRE"] + half
    c2_top = p["CROSS2_CENTRE"] - half
    c2_bot = p["CROSS2_CENTRE"] + half

    same_face_overlap = _overlap(c1_top, c1_bot, c2_top, c2_bot)
    ok = not same_face_overlap

    detail = (f"CROSS1=[{c1_top:.2f}, {c1_bot:.2f}] vs "
              f"CROSS2=[{c2_top:.2f}, {c2_bot:.2f}]: "
              f"{'height overlap — FAIL' if same_face_overlap else 'no height overlap — PASS'}")
    return (_pass("I-3", detail) if ok else _fail("I-3", detail))


# ---------------------------------------------------------------------------
# I-11: Crossbar mortise clears corner tab zone
# ---------------------------------------------------------------------------

def inv_crossbar_mortises_clear_corner_zone(p: dict) -> tuple:
    """
    I-11: All crossbar mortise height spans must be > MAT from each stile end.

    The corner tab zone occupies [0, MAT] at the stile top end and
    [STILE_BODY_H - MAT, STILE_BODY_H] at the stile bottom end.
    A mortise entering this zone would intersect the finger joint geometry.

    Proof: for each crossbar mortise [centre - half, centre + half]:
      top clearance  = (centre - half) - 0          > MAT
      bottom clearance = STILE_BODY_H - (centre + half) > MAT
    """
    half = p["CROSS_MORT_W"] / 2
    mat = p["MAT"]
    body_h = p["STILE_BODY_H"]

    results = []
    ok_all = True
    for name, centre in [("CROSS1", p["CROSS1_CENTRE"]), ("CROSS2", p["CROSS2_CENTRE"])]:
        top_clr = (centre - half) - 0.0
        bot_clr = body_h - (centre + half)
        ok_top = top_clr > mat
        ok_bot = bot_clr > mat
        ok = ok_top and ok_bot
        ok_all = ok_all and ok
        results.append(
            f"{name}: top_clr={top_clr:.2f}>{mat}={'OK' if ok_top else 'FAIL'}, "
            f"bot_clr={bot_clr:.2f}>{mat}={'OK' if ok_bot else 'FAIL'}"
        )

    trace = "; ".join(results)
    return (True, f"PASS  I-11: {trace}") if ok_all else (False, f"FAIL  I-11: {trace}")


# ---------------------------------------------------------------------------
# I-10: Box interior holds all loom parts
# ---------------------------------------------------------------------------

def inv_box_interior_holds_loom(p: dict) -> tuple:
    """
    I-10: Box interior dimensions accommodate all loom parts in a single flat layer.

    Longest part = stile (STILE_TOTAL_H).
    Interior length must be >= STILE_TOTAL_H + 2mm clearance.
    Interior height must be >= MAT + 2mm clearance (single 6mm layer).
    Interior width is checked against the pack_width estimate; refined in verify_box.py.
    """
    longest = p["STILE_TOTAL_H"]
    clearance = 2.0
    ok_l = p["BOX_INTERIOR_L"] >= longest + clearance
    ok_h = p["BOX_INTERIOR_H"] >= p["MAT"] + clearance
    ok_w = p["BOX_INTERIOR_W"] >= p["BOX_PACK_W_ESTIMATE"]
    ok = ok_l and ok_h and ok_w

    detail = (
        f"length: {p['BOX_INTERIOR_L']:.1f}>={longest:.1f}+{clearance}={'OK' if ok_l else 'FAIL'}; "
        f"height: {p['BOX_INTERIOR_H']:.1f}>={p['MAT']+clearance:.1f}={'OK' if ok_h else 'FAIL'}; "
        f"width: {p['BOX_INTERIOR_W']:.1f}>={p['BOX_PACK_W_ESTIMATE']:.1f}={'OK' if ok_w else 'FAIL'}"
    )
    return (_pass("I-10", detail) if ok else _fail("I-10", detail))


# ---------------------------------------------------------------------------
# I-1 (partial): Critical parts fit within sheet bounds (without full layout)
# ---------------------------------------------------------------------------

def inv_critical_parts_fit_sheet(p: dict) -> tuple:
    """
    I-1 (partial): The two most space-constrained parts (stile, rail) fit within their sheet.
    Full layout check (all parts, no overlaps) lives in verify_loom.py.

    Stile total height + 2*MARGIN <= SHEET_H
    Rail total length + 2*MARGIN  <= SHEET_W
    Two stiles side by side (2*STILE_W + 2*MARGIN + part_gap) <= SHEET_W
    """
    margin = p["MARGIN"]
    ok_stile_h = p["STILE_TOTAL_H"] + 2 * margin <= p["SHEET_H"]
    ok_rail_w = p["FRAME_OUTER_W"] + 2 * margin <= p["SHEET_W"]
    # Two stiles side by side (D-13: clean outline, no protrusions)
    two_stiles_w = 2 * p["STILE_W"] + margin
    ok_two_stiles = two_stiles_w + 2 * margin <= p["SHEET_W"]

    ok = ok_stile_h and ok_rail_w and ok_two_stiles
    detail = (
        f"stile_h: {p['STILE_TOTAL_H']:.1f}+{2*margin}={p['STILE_TOTAL_H']+2*margin:.1f}<={p['SHEET_H']}={'OK' if ok_stile_h else 'FAIL'}; "
        f"rail_w: {p['FRAME_OUTER_W']:.1f}+{2*margin}<={p['SHEET_W']}={'OK' if ok_rail_w else 'FAIL'}; "
        f"2×stile: {two_stiles_w:.1f}+{2*margin}<={p['SHEET_W']}={'OK' if ok_two_stiles else 'FAIL'}"
    )
    return (_pass("I-1-partial", detail) if ok else _fail("I-1-partial", detail))


# ---------------------------------------------------------------------------
# I-5b: Crossbar tenon geometry consistent
# ---------------------------------------------------------------------------

def inv_crossbar_geometry(p: dict) -> tuple:
    """
    I-5b: Crossbar geometry (D-13: no-tenon design).
    CROSS_TOTAL_L == CROSS_BODY_W (= INTERIOR_W, no tenons).
    Stile pocket depth: STILE_W - CROSS_MORT_D >= MAT (minimum remaining material).
    CROSS_H > MAT (crossbar taller than material thickness for stiffness).
    """
    ok_total = abs(p["CROSS_TOTAL_L"] - p["CROSS_BODY_W"]) < 1e-9
    remaining = p["STILE_W"] - p["CROSS_MORT_D"]
    ok_remaining = remaining >= p["MAT"]
    ok_height = p["CROSS_H"] > p["MAT"]

    ok = ok_total and ok_remaining and ok_height
    detail = (
        f"total={p['CROSS_TOTAL_L']:.1f}==body={p['CROSS_BODY_W']:.1f}={'OK' if ok_total else 'FAIL'}; "
        f"remaining stile={remaining:.1f}>={p['MAT']:.1f}={'OK' if ok_remaining else 'FAIL'}; "
        f"CROSS_H={p['CROSS_H']:.1f}>MAT={p['MAT']:.1f}={'OK' if ok_height else 'FAIL'}"
    )
    return (_pass("I-5b", detail) if ok else _fail("I-5b", detail))


# ---------------------------------------------------------------------------
# I-5c: Stand notch geometry
# ---------------------------------------------------------------------------

def inv_stand_notch_geometry(p: dict) -> tuple:
    """
    I-5c: Stand X-piece joint geometry (D-23, triangular piece).
    STAND_X_SLOT_W in [MAT+0.05, MAT+0.5] — clearance fit for cross-halving.
    STAND_X_SLOT_D == STAND_X_W/4 ± 0.5 — half of triangle height at slot_cx.
    STAND_X_TAB_L in [15, 40] — foot tab length plausible.
    STAND_X_TAB_H in [10, STAND_X_W/2] — tab height at most half the foot width.
    STAND_X_BUMP_H in [2, 10] — bump height plausible.
    """
    mat   = p["MAT"]
    sw    = p["STAND_X_SLOT_W"]
    sd    = p["STAND_X_SLOT_D"]
    xw    = p["STAND_X_W"]
    tab_l = p["STAND_X_TAB_L"]
    tab_h = p["STAND_X_TAB_H"]
    bump_h = p["STAND_X_BUMP_H"]

    ok_sw  = mat + 0.05 <= sw <= mat + 0.5
    ok_sd  = abs(sd - xw / 4.0) <= 0.5           # slot_d = W/4 ± 0.5
    ok_tab_l = 15.0 <= tab_l <= 40.0
    ok_tab_h = 10.0 <= tab_h <= xw / 2.0
    ok_bump  = 2.0 <= bump_h <= 10.0
    ok = ok_sw and ok_sd and ok_tab_l and ok_tab_h and ok_bump

    detail = (
        f"slot_w={sw:.2f} in [{mat+0.05:.2f},{mat+0.5:.2f}]={'OK' if ok_sw else 'FAIL'}; "
        f"slot_d={sd:.2f}~=W/4={xw/4:.2f}={'OK' if ok_sd else 'FAIL'}; "
        f"tab_l={tab_l:.1f} in [15,40]={'OK' if ok_tab_l else 'FAIL'}; "
        f"tab_h={tab_h:.1f} in [10,{xw/2:.1f}]={'OK' if ok_tab_h else 'FAIL'}; "
        f"bump_h={bump_h:.1f} in [2,10]={'OK' if ok_bump else 'FAIL'}"
    )
    return (_pass("I-5c", detail) if ok else _fail("I-5c", detail))


# ---------------------------------------------------------------------------
# I-14: Corner radii positive (D-39)
# ---------------------------------------------------------------------------

def inv_corner_r_positive(p: dict) -> tuple:
    """
    I-14: CORNER_R > 0 AND HEDDLE_BAR_CORNER_R > 0
    Thread-contact parts (rail notches, beater teeth, heddle bar) must have rounded
    corners so warp and weft threads slide without snagging or abrasion. D-39.
    """
    cr  = p["CORNER_R"]
    hcr = p["HEDDLE_BAR_CORNER_R"]
    ok_cr  = cr  > 0.0
    ok_hcr = hcr > 0.0
    ok = ok_cr and ok_hcr
    detail = (f"CORNER_R={cr:.3f}>0={'OK' if ok_cr else 'FAIL'}; "
              f"HEDDLE_BAR_CORNER_R={hcr:.3f}>0={'OK' if ok_hcr else 'FAIL'}")
    return (_pass("I-14", detail) if ok else _fail("I-14", detail))


# ---------------------------------------------------------------------------
# I-13: Beater tooth min width (D-37)
# ---------------------------------------------------------------------------

def inv_beater_tooth_min_width(p: dict) -> tuple:
    """
    I-13: BEATER_TOOTH_W >= BEATER_MIN_TOOTH_W
    Beater tooth must be at least BEATER_MIN_TOOTH_W wide to survive handling in the
    target material. D-37: default floor = 4mm for 6mm birch ply.
    Override via min_tooth_w knob for stronger materials (acrylic, CNC metal).
    """
    tw = p["BEATER_TOOTH_W"]
    mw = p["BEATER_MIN_TOOTH_W"]
    detail = f"BEATER_TOOTH_W={tw:.4f} >= BEATER_MIN_TOOTH_W={mw:.4f}"
    return (_pass("I-13", detail) if tw >= mw else _fail("I-13", detail))


# ---------------------------------------------------------------------------
# Master scan
# ---------------------------------------------------------------------------

ALL_INVARIANTS = [
    ("I-4  tab < stile_w",             inv_tab_narrower_than_stile),
    ("I-5  tab > MAT",                 inv_tab_wider_than_mat),
    ("I-5b crossbar geometry (D-13)",  inv_crossbar_geometry),
    ("I-5c stand notch geometry",      inv_stand_notch_geometry),
    ("I-6  sock > tab",                inv_socket_wider_than_tab),
    ("I-7  clearance in range",        inv_clearance_in_range),
    ("I-8  notch count*pitch=span",    inv_notch_count_pitch_span),
    ("I-8b notch positions in rail",   inv_notch_positions_within_rail),
    ("I-9  notch_depth < rail_w",      inv_notch_depth_less_than_rail),
    ("I-3  no mortise 3D intersect",   inv_no_mortise_3d_intersection),
    ("I-11 crossbar clears corner",    inv_crossbar_mortises_clear_corner_zone),
    ("I-10 box holds loom",            inv_box_interior_holds_loom),
    ("I-1  critical parts fit sheet",  inv_critical_parts_fit_sheet),
    ("I-13 beater tooth min width",    inv_beater_tooth_min_width),
    ("I-14 corner radii positive",     inv_corner_r_positive),
]


def check_all(p: dict) -> list:
    """Run all invariants. Returns list of (name, ok, trace)."""
    return [(name, *fn(p)) for name, fn in ALL_INVARIANTS]


def assert_all(p: dict) -> None:
    """Run all invariants; raise AssertionError listing every failure."""
    results = check_all(p)
    failures = [(name, trace) for name, ok, trace in results if not ok]
    if failures:
        lines = "\n".join(f"  {name}: {trace}" for name, trace in failures)
        raise AssertionError(f"INVARIANT FAILURES ({len(failures)}):\n{lines}")


def print_report(p: dict) -> bool:
    """Run all invariants and print a formatted report. Returns True if all pass."""
    results = check_all(p)
    all_pass = all(ok for _, ok, _ in results)
    print(f"\n{'='*60}")
    print(f"INVARIANT REPORT  ({'ALL PASS' if all_pass else 'FAILURES FOUND'})")
    print(f"{'='*60}")
    for name, ok, trace in results:
        print(f"  {'✓' if ok else '✗'} {trace}")
    print(f"{'='*60}\n")
    return all_pass
