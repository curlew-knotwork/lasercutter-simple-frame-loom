# Design Decisions
**Version:** 2
**Date:** 2026-03-06
**Status:** ACTIVE — decisions locked from sparring round 1

Decisions are immutable once locked. If a decision must change, add a superseding entry and strike through the old one. Never silently overwrite.

---

## Locked Decisions

### D-01 — N=1 finger tab per corner joint
- **Decision:** One central tab per corner finger joint.
- **Rationale:** N=2 gives tab_width = 22/5 = 4.4mm < MAT=6mm — structurally inadequate. N=1 gives 22/3 = 7.33mm > 6mm ✓.
- **Invariant:** `tab_width = STILE_W / (2×N+1) > MAT` must hold for chosen N.
- **Locked:** 2026-03-06

### D-02 — Warp notch shape: U-bottom rectangular
- **Decision:** All warp notches are rectangular (flat bottom), not V-shaped.
- **Rationale:** V-notches abrade or cut yarn, especially fine yarn. U-notches hold yarn safely in the flat base.
- **Locked:** 2026-03-06

### D-03 — Nominal material thickness: MAT=6mm (loom), MAT3=3mm (box and stand)
- **Decision:** Design nominally for 6mm loom sheet and 3mm box/stand sheet. Actual thickness verified by fit test before full cut.
- **Locked:** 2026-03-06

### D-04 — Kerf assumption: 0.15mm per cut side (0.30mm total per slot)
- **Decision:** All drawn tab widths reduced by 2×kerf relative to nominal; all drawn socket widths enlarged by 2×kerf. Verified by fit test.
- **Tab drawn width:** TAB_W = nominal − 0 (laser removes kerf from both sides of tab)
- **Socket drawn width:** SOCK_W = nominal + 0.1mm clearance (net after kerf)
- **Fit test** verifies before committing either full sheet.
- **Locked:** 2026-03-06

### D-05 — Interior weaving area: 300×400mm
- **Decision:** Default interior weaving area is 300mm wide × 400mm tall.
- **Rationale:** Suitable for a scarf panel or medium wall hanging; fits a 600×600mm sheet with all accessories.
- **Derived dimensions:**
  - Frame outer width: 344mm
  - Frame outer height: 444mm
  - Stile body height: 444mm; total with tabs: 456mm
  - Rail total length (with socket protrusions): 356.2mm
  - Crossbar total length: 330mm (300mm body + 15mm tenon each end)
- **Locked:** 2026-03-06

### D-06 — Warp notches: 31 notches, 10mm pitch, on top and bottom rails only
- **Decision:** 31 warp notches, 10mm centre-to-centre pitch, U-bottom, 4mm wide, 5mm deep.
  - Top rail: notches open downward (toward weaving interior)
  - Bottom rail: notches open upward (toward weaving interior)
  - No notches on intermediate crossbars.
- **Invariant:** `(notch_count − 1) × pitch == INTERIOR_W` → (31−1) × 10 = 300 ✓
- **Notch centreline positions:** x = STILE_W + k×pitch for k = 0, 1, …, 30
  - First centreline: 22mm from rail outer edge (= inner stile face)
  - Last centreline: 322mm from rail outer edge (= other inner stile face)
- **Locked:** 2026-03-06

### ~~D-07 — Intermediate crossbars (original)~~ SUPERSEDED by D-13
- **Original decision:** Crossbars CROSS_H=MAT=6mm, tenon+mortise edge-slot connection.
- **Superseded:** 2026-03-06 → see D-13.

### D-08 — No prop mortises in loom stiles; stand is independent
- **Decision:** The loom frame has NO prop/kickstand mortises. The stand is a completely separate assembly. The loom rests in angled notches on the stand. Stiles carry only: corner finger-joint tabs (top and bottom) and two inner-face crossbar mortises.
- **Rationale:** Eliminates the mortise overlap problem (DEF-002, DEF-005). Cleaner stile geometry. More robust and stable stand.
- **Locked:** 2026-03-06

### ~~D-09 — Stand material: 3mm birch plywood; stand on box sheet~~ SUPERSEDED by D-16
- **Original decision:** Stand on box sheet (3mm ply).
- **Superseded:** 2026-03-07 → see D-16.

### ~~D-10 — Stand type: A-frame easel, three pieces~~ SUPERSEDED by D-18
- **Original decision:** Stand-L, Stand-R (mirror), Stand-Spreader. Each leg with angled U-notch (25° from vertical) to cradle a loom stile. Never implemented.
- **Superseded:** 2026-03-07 → see D-18 (solid right-triangle sides + 6 cross members).

### D-11 — Each cut piece is a single unified closed-outline path
- **Decision:** Every laser-cut piece has exactly one outer boundary path (a single closed polygon). Internal voids (holes, lightening ellipses, grip holes) are separate closed paths nested inside the outer boundary path. No piece is represented as a collection of overlapping rectangles or open paths.
- **Rationale:** Laser cutter follows paths in order. A single closed outer path ensures the piece is cut out in one pass. Internal holes are cut separately. Overlapping paths cause double-cutting and dimensional errors.
- **Enforcement:** verify.py must confirm each piece path is closed (M...Z) and that no two outer paths of different pieces intersect.
- **Locked:** 2026-03-06

### D-12 — Hard geometric invariants (no exceptions)
The following invariants must hold for every valid parameter set. Any parameter combination that violates an invariant is INVALID and must raise an error before any SVG is written.

| # | Invariant | Formula |
|---|---|---|
| I-1 | All parts within sheet bounds | ∀ part p: bounding_box(p) ⊆ [MARGIN, SHEET_W−MARGIN] × [MARGIN, SHEET_H−MARGIN] |
| I-2 | No part overlap on sheet | ∀ parts p≠q: interior(bbox(p)) ∩ interior(bbox(q)) = ∅ |
| I-3 | No mortise 3D intersection | ∀ mortise pairs (m1,m2) on same member: height_ranges_overlap(m1,m2) → depth(m1)+depth(m2) < member_width |
| I-4 | Tab narrower than member width | tab_width < STILE_W |
| I-5 | Tab wider than material thickness | tab_width > MAT |
| I-6 | Socket wider than tab | SOCK_W > TAB_W |
| I-7 | Clearance in range | 0.05mm ≤ SOCK_W − TAB_W ≤ 0.40mm |
| I-8 | Notch count/pitch/span consistent | (notch_count − 1) × notch_pitch == INTERIOR_W |
| I-9 | Notch does not exceed rail depth | notch_depth < RAIL_W |
| I-10 | Box interior holds all loom parts | box_interior_L ≥ max(part_length) + CLEARANCE; box_interior_W ≥ pack_width(all_parts) + CLEARANCE; box_interior_H ≥ MAT + CLEARANCE |
| I-11 | Crossbar mortise clear of corner tab zone | crossbar_mortise_top > corner_tab_zone_bottom (i.e., > MAT from stile end) |
| I-12 | Outer path of each piece is closed | All cut paths end with Z; no open strokes |

- **Locked:** 2026-03-06

---

### D-13 — Crossbar: CROSS_H=20mm, closed rect-hole mortise, no tenon
- **Decision:** CROSS_H = 20mm (was MAT=6mm). Crossbar body = INTERIOR_W exactly (no tenons). CROSS_TOTAL_L = INTERIOR_W = 300mm.
- **Mortise:** Closed rectangular through-hole in stile body at crossbar y-position (not open edge slot). Hole: CROSS_MORT_D (5mm) × CROSS_MORT_W (CROSS_H+0.1 = 20.1mm). Accessed from stile inner face before rails are assembled.
- **Rationale:** Closed hole leaves stile edge intact (stronger than open slot). 20mm height gives ~37× bending stiffness vs 6mm. Assembled before rails: crossbar slides into holes from inner face before top/bottom rail is attached.
- **Stile outline:** Clean rectangle + tab protrusions. No concave mortise indentations. Crossbar mortise positions represented as rect_holes (separate laser-cut paths), not polygon dips.
- **Locked:** 2026-03-06

### D-14 — Box interior height: 12mm
- **Decision:** BOX_INTERIOR_H = 12mm (was MAT+2=8mm). Provides comfortable clearance for loom parts lying flat (all parts ≤ MAT=6mm thick when flat). Enables cleaner finger-joint geometry on 3mm ply box walls (tab = MAT3 = 3mm gives N=2 tabs on 12mm walls).
- **Locked:** 2026-03-06

### D-15 — Box joint design: wall-to-wall finger joints + wall-to-base edge tabs + sliding lid
- **Wall-to-wall corners:** N=1 finger joint per corner (short wall has tab, long wall has socket). Tab = BOX_TAB_W = 4mm wide, MAT3 = 3mm deep.
- **Wall-to-base:** Each wall bottom edge has N tabs protruding MAT3=3mm downward; base has matching edge notches (concave, opens at base perimeter edge). Tab width = BOX_TAB_W = 4mm for all base tabs.
  - Long walls: BOX_BASE_NTABS_L = **15** tabs evenly spaced.
  - Short walls: BOX_BASE_NTABS_S = **5** tabs evenly spaced.
  - (Previous D-15 text said 3/1; code used max(8, round(len/22)) giving 21/12. Corrected to 15/5 by D-20 decision.)
- **Lid:** Flat panel (BOX_INTERIOR_L × BOX_INTERIOR_W) slides through BOX_DADO_W = 3.2mm slots at top of short walls. Lid enters from one short-wall end.
- **No glue, no hardware** — all joints press-fit.
- **Assembly sequence:** Connect 4 walls at corners → lower base onto wall bottom tabs from above → slide lid in.
- **Locked:** 2026-03-06; tab counts corrected 2026-03-08 per D-20.

---

### D-16 — Stand: separate optional SVG, 6mm ply, two spreaders
- **Decision:** The A-frame stand is optional. It is generated as `output/optional_loom_stand.svg`, a separate 600×600mm 6mm birch ply sheet. It is not included on the loom or box sheets.
- **Rationale:** Not everyone will use the stand. Making it optional avoids wasting material. 6mm ply (same as loom) gives better rigidity than 3mm. Removing stand from box sheet simplifies that layout. Keeping the default loom at 300×400mm (scarf size) remains the primary output.
- **Material:** MAT = 6mm (same sheet stock as the loom).
- **Parts:** Stand-L, Stand-R (mirror), Stand-Spreader × 2 (same piece cut twice).
- **Two spreaders:** one near the top of each leg (centre 50mm from leg top, below U-notch), one near the bottom (centre 30mm from leg bottom). Two spreaders at different heights triangulate the frame, eliminating the racking mode that a single spreader cannot resist. Same spreader piece cut twice.
- **Leg mortises:** two rectangular holes per leg, same width `STAND_SPREAD_MORT_W = MAT + 0.1 = 6.1mm`, same depth `STAND_SPREAD_MORT_D = 15mm`. Upper mortise centre at `STAND_MORT_Y_TOP = 50mm` from leg top; lower mortise centre at `STAND_MORT_Y_BOT = 30mm` from leg bottom.
- **Mortise change from D-09:** `STAND_SPREAD_MORT_W = MAT + 0.1 = 6.1mm` (was MAT3+0.1=3.1mm).
- **Generator:** `src/stand.py` → `output/optional_loom_stand.svg`.
- **Total sheets:** loom.svg (6mm), box.svg (3mm), optional_loom_stand.svg (6mm, cut only if wanted), test_cut.svg (3mm scrap).
- **Locked:** 2026-03-07

### D-17 — Stand: triangle L-bracket, top rail slot connection
- **Supersedes:** D-16.
- **SUPERSEDED BY D-18.**
- **Locked:** 2026-03-07

### ~~D-18 — Stand: solid right-triangle side pieces, edge-notch cross members~~ SUPERSEDED by D-22
- **Supersedes:** D-17.
- **Design:** Two solid right-triangle side pieces (Stand-L, Stand-R mirror) + 5 cross members. Output: `output/optional_loom_stand.svg`, 6mm birch ply, 600×600mm.
- **Triangle geometry:** Right angle at bottom-back corner. Vertices (local): (0,0) top-back, (0,420) bottom-back, (240,420) bottom-front. Bounding box: STAND_BASE_L=240mm × STAND_UPRIGHT_H=420mm. 3 rectangular edge notches in upright (rear/left) edge: STAND_NOTCH_W=30.1mm wide × STAND_NOTCH_D=15mm deep, centred at y=60, 210, 360mm from top (STAND_MORT_Y_TOP, STAND_MORT_Y_MID, STAND_MORT_Y_BOT). 2 edge notches in base (bottom) edge: same dimensions, centred at x=80, 160mm from back end (STAND_BASE_NOTCH_X1, STAND_BASE_NOTCH_X2). Stand-R is mirror of Stand-L about its own centre x.
- **Cross members (×5, same cut dimensions):** STAND_SPREAD_L + 2×STAND_SPREAD_TEN_L = 344+30 = 374mm total × STAND_SPREAD_W=30mm wide. The 15mm each end slides into the triangle edge notch (edge-notch joinery, no separate tenon geometry). No holes.
  - stand_rear_cross_1 (y=60): WITH stile slots.
  - stand_rear_cross_2 (y=210): structural only, no stile slots.
  - stand_rear_cross_3 (y=360): WITH stile slots.
  - stand_base_cross_1 (base at x=80): no stile slots.
  - stand_base_cross_2 (base at x=160): no stile slots.
- **Stile slots** (in loom-facing/top edge of rear cross 1 and 3): STAND_STILE_SLOT_W=22.5mm × STAND_STILE_SLOT_D=15mm concave cutouts. Centres at x=STAND_SPREAD_TEN_L+STAND_STILE_SLOT_W/2 (left) and x=total_l−STAND_SPREAD_TEN_L−STAND_STILE_SLOT_W/2 (right). Slot aligns with STILE_W=22mm loom stile + 0.25mm clearance each side.
- **Loom connection:** Loom stiles drop into stile slots of rear cross members. No top-rail extensions needed. STAND_RAIL_TAB_L=0 (top rail reverts to FRAME_OUTER_W=344mm).
- **STAND_SPREAD_MORT_W=30.1mm, STAND_SPREAD_MORT_D=15mm** (edge notch fit for cross member body).
- **Sheet layout:** Triangles side-by-side at y=2..422 (×2); 5 cross members stacked at y=424..582. All within 600×600mm sheet.
- **Box rename:** `output/box.svg` → `output/optional_box.svg` (carried forward from D-17).
- **Locked:** 2026-03-07

### ~~D-19 — Stand joint redesign: L-shaped drop-Z upright notches + hypotenuse cross member~~ SUPERSEDED by D-22
- **Supersedes:** D-18 joint geometry (notch shape and cross member count only; triangle shape and dimensions unchanged).
- **Upright edge notches — L-shaped entry:** Each upright-edge notch gains a 2mm-tall entry zone (STAND_NOTCH_ENTRY=2mm) at partial depth (STAND_NOTCH_ENTRY_D=8mm). Cross member slides in horizontally; at x=8mm the step blocks further entry until cross member drops 2mm (gravity); cross member then seats in 30.1mm captive zone at full 15mm depth. Prevents vibration/loosening during use.
- **STAND_NOTCH_W unchanged at 30.1mm.** This matches the 30mm cross member HEIGHT (not thickness). The 6mm cross member thickness leaves 9mm of play in the notch depth direction; the L-shape eliminates vertical play.
- **Hypotenuse cross member:** One additional plain cross member (same cut dimensions: 374×30mm) connecting the two triangles via a parallelogram notch cut into each triangle's hypotenuse edge. Centre at t=0.25 from top vertex: local (STAND_HYP_CX=60mm, STAND_HYP_CY=105mm). Notch is a parallelogram (4 pts rotated 29.7° from horizontal), width STAND_NOTCH_W=30.1mm × depth STAND_NOTCH_D=15mm, perpendicular to hyp. Prevents triangle tops from spreading/leaning under loom load.
- **REAR X0 (y=40mm) NOT added:** Notch at y=40 overlaps REAR X1 at y=60 (30.1mm notch width; gap between notch edges = -10mm). Hyp cross member provides equivalent top constraint.
- **Total cross members: 6** (REAR X1/X2/X3 + BASE X1/X2 + HYP).
- **Layout:** 5 horizontal cross members stacked below triangles; 1 hyp cross member placed rotated 90° to the right of both triangles (30mm wide × 374mm tall on sheet).
- **Base edge notches:** plain rectangular (unchanged); assembly = triangles drop onto base cross members, no L-shape needed.
- **Locked:** 2026-03-07

### ~~D-20 — Stand: easel lean, upright base cross members~~ SUPERSEDED by D-21, then D-22
- **Decision:** Stand functions as easel. BASE cross members oriented upright (30mm height vertical, 6mm on table). Triangle base notches: STAND_BASE_NOTCH_W = MAT+0.1 = 6.1mm. Stile slots removed from all cross members. Loom bottom rail on BASE X2 front face (~24°); stile back on REAR X1 face.
- **Superseded by D-21.**
- **Locked:** 2026-03-08

### ~~D-21 — Stand: BASE cross members lie flat, shallow base notches~~ SUPERSEDED by D-22
- **Supersedes:** D-20 base notch geometry only. Easel lean and stile slot removal unchanged.
- **Problem with D-20:** Upright base cross members elevated both triangles 15mm above table on narrow feet — unstable and incorrect.
- **Decision:** BASE cross members lie **flat** (same 2D cut as REAR — 374×30mm rectangle, no change to shape). Triangle base edge notches: STAND_BASE_NOTCH_W = STAND_NOTCH_W = 30.1mm (grips 30mm face), STAND_BASE_NOTCH_D = MAT = 6mm (shallow — cross member seated flush with base edge). No L-shaped entry on base notches — open at floor, gravity retains.
- **Result:** Triangle base edges and cross member bottom faces all coplanar at floor level. Lean geometry unchanged: BASE X2 front face at x≈175mm from back → ~24° lean.
- **Locked:** 2026-03-08

### ~~D-22 — Stand: 2-piece Standing X easel (supersedes D-18/D-19/D-20/D-21)~~ SUPERSEDED by D-23
- **Supersedes:** D-18, D-19, D-20, D-21 (all prior stand geometry).
- **Design:** Two identical 6mm ply pieces, cross-halving half-lap joint at centre. Output: `output/optional_loom_stand.svg`, 6mm birch ply, 600×600mm.
- **Piece geometry (STAND_X_L × STAND_X_W = 450×80mm):** Rectangle with two concave notches:
  1. **Cross-halving slot:** top edge (y=0), centred at x=L/2=225mm, STAND_X_SLOT_W=6.1mm wide × STAND_X_SLOT_D=40mm deep. One piece assembled with slot-up, the other flipped 180° (slot-down). They interlock to form the X.
  2. **Rail notch:** bottom-left corner, STAND_X_RAIL_NOTCH_W=22.5mm wide × STAND_X_RAIL_NOTCH_D=6mm deep. Captures loom bottom rail (RAIL_W=22mm) on the rear arm foot. When piece is flipped for front arm, notch is at upper harmless position.
- **Assembly:** Stand fits inside loom interior (300mm wide, stand is 80mm wide). Loom frame provides left-right stability. Lean angle (~24°) set naturally by weight distribution.
- **Flat-pack:** Two pieces (450×80mm each) fit side-by-side in box layer 2 (6mm above loom parts): 450×160mm < BOX_INTERIOR_L×BOX_INTERIOR_W ✓. Pieces store WITH the loom in its box.
- **Sheet layout:** Both pieces horizontal, stacked vertically on 600×600mm sheet. Leaves significant space on sheet (pieces are 450×160mm total).
- **Params:** STAND_X_L=450mm, STAND_X_W=80mm, STAND_X_SLOT_W=MAT+0.1=6.1mm, STAND_X_SLOT_D=STAND_X_W/2=40mm, STAND_X_RAIL_NOTCH_W=RAIL_W+0.5=22.5mm, STAND_X_RAIL_NOTCH_D=MAT=6mm.
- **Locked:** 2026-03-08

### D-23 — Stand: 2-piece triangular X easel (supersedes D-22)
- **Supersedes:** D-22 (rectangular piece geometry).
- **Design:** ONE cut pattern, TWO identical pieces cut from it. One piece is flipped 180° in the plane for assembly. Output: `output/optional_loom_stand.svg`, 6mm birch ply, 600×600mm. Layout = 2 copies of the same polygon; no separate piece-B function.
- **Piece geometry (right triangle + hypotenuse foot tab + bump):**
  - **Triangle:** Right angle at (0,0). Top edge horizontal: (0,0)→(L,0). Hypotenuse: (L,0)→(0,W). Foot edge vertical: (0,W)→(0,0).
  - **Cross-halving slot:** from top edge (y=0) at x=L/2=225mm, STAND_X_SLOT_W=6.1mm wide × STAND_X_SLOT_D=W/4=20mm deep. At x=L/2, triangle height=W/2=40mm; slot depth=half that=20mm. Piece A slot-up, piece B flipped 180° so slot opens downward. They interlock at the crossing.
  - **Foot tab:** protrudes from the HYPOTENUSE edge at the foot end (near (0,W)), outward (away from triangle interior, in +y direction). Tab is a rectangular protrusion from the hyp body — connected along the hyp edge, not at a corner point — so it has material support. Tab depth (along hyp) = STAND_X_TAB_L=25mm; tab height (perpendicular to hyp, into +y) = STAND_X_TAB_H=20mm.
  - **Bump:** Mechanical stop at outer end of tab. STAND_X_BUMP_L=5mm × STAND_X_BUMP_H=5mm step at tip of tab. Prevents loom bottom rail from sliding off.
- **Assembly:** Piece B is piece A rotated 180° in-plane. Slots interlock at x=L/2. Stand stands on short legs; foot tabs on hypotenuse cradle loom bottom rail.
- **Flat-pack:** Each piece bbox ≈ STAND_X_L × (STAND_X_W + STAND_X_TAB_H) = 450×100mm (approx; exact from geometry). Two pieces stacked with gap.
- **Sheet layout:** Both pieces horizontal, stacked vertically at y=MARGIN and y=MARGIN+piece_h+GAP.
- **Params:** STAND_X_L=450mm, STAND_X_W=80mm, STAND_X_SLOT_W=MAT+0.1=6.1mm, STAND_X_SLOT_D=STAND_X_W/4=20mm, STAND_X_TAB_L=25mm, STAND_X_TAB_H=20mm, STAND_X_BUMP_L=5mm, STAND_X_BUMP_H=5mm.
- **Locked:** 2026-03-15

---

## Superseded Decisions

- D-07 (original crossbar design): superseded by D-13.
- D-09 (stand on box sheet, 3mm ply): superseded by D-16.
- D-16 (rectangular leg stand, rail U-notch for stile): superseded by D-17.
- D-17 (L-bracket stand, top-rail tabs, X stiffener bars): superseded by D-18.
- D-10 (A-frame easel, U-notch stile cradle): superseded by D-18.
- D-18 (triangle side pieces + 6 cross members): superseded by D-22.
- D-19 (L-shaped upright notches + hyp cross member): superseded by D-22.
- D-20 (upright base cross members, STAND_BASE_NOTCH_W=6.1mm): superseded by D-21, then D-22.
- D-21 (BASE cross members flat, wide shallow notches): superseded by D-22.
