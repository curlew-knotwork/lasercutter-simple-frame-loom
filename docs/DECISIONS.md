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

### D-09 — Stand material: 3mm birch plywood; stand on box sheet
- **Decision:** The easel stand is cut from 3mm birch plywood. Stand pieces are nested on the box SVG sheet (not the loom sheet). If they do not fit on the box sheet, a third 3mm sheet is used.
- **Rationale:** User confirmed 3mm is sufficiently stable. 3mm stand shares material with the box, reducing sheet count.
- **Total sheets:** loom.svg (6mm), box.svg (3mm, includes stand pieces), test_cut.svg (3mm scrap).
- **Locked:** 2026-03-06

### D-10 — Stand type: A-frame easel, three pieces
- **Decision:** Stand consists of Stand-L, Stand-R (mirror), and Stand-Spreader. Stand-L and Stand-R each have an angled U-notch (25° from vertical = 65° from horizontal) that cradles one stile. The spreader connects the two side pieces to prevent splay. Loom rests in the notches by gravity; warp tension holds it in place.
- **Locked:** 2026-03-06

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

---

## Superseded Decisions

- D-07 (original crossbar design): superseded by D-13.
