# Design — Open Questions and Proposals
**Version:** 2
**Date:** 2026-03-06
**Status:** SPARRING — Q1, Q2, Q3 answered by user; updating proposals

Decisions that survive sparring are moved to DECISIONS.md.
This file retains all questions (open and closed) for audit trail.

---

## Question Register

| ID | Question | Status | Decision |
|---|---|---|---|
| Q1 | Interior weaving area | ANSWERED | 300×400mm preferred; sheet fit check required |
| Q2 | Intermediate crossbar type | ANSWERED | Structural only; notches on top/bottom rails only (conventional wisdom) |
| Q3 | Prop/stand type | SUPERSEDED | D-23: 2-piece triangular X easel, 6mm ply |
| Q4 | Warp notch pitch and count | SUPERSEDED | D-24: 61 notches, 5mm pitch |
| Q5 | Heddle bar: flat laser-cut vs round dowel | OPEN | Flat bar proposed |
| Q6 | Shuttle count | OPEN | 2 proposed |
| Q7 | Beater span | OPEN | Pending Q4 resolution |
| Q8 | Warp notch shape | PRE-DECIDED | U-bottom rectangular |
| Q9 | Finger joint count per corner | PRE-DECIDED | N=1 only viable option |
| Q10 | Actual material thickness assumption | PRE-DECIDED | MAT=6mm nominal; fit test verifies |
| Q11 | 3D mortise conflict check | RESOLVED | No conflicts in 2-crossbar design |
| Q12 | Old SVG files: archive or delete | OPEN | Archive proposed |
| Q13 | Stroke width convention | OPEN | Low priority |
| Q14 | Sheet fit for 300×400mm interior | NEW — OPEN | Analysis below |
| Q15 | Stand design for tall frame (444mm) | SUPERSEDED | D-23: 2-piece triangular X easel |

---

## Q1 — Interior Weaving Area (UPDATED)

**User answer:** 300×400mm for scarf preferred. Check if all pieces fit on one sheet.

**Frame dimensions at 300×400mm interior:**
- Stile width (STILE_W): 22mm (unchanged from analysis — N=1 gives 7.33mm tab, valid)
- Rail width (RAIL_W): 22mm
- Frame outer width: 300 + 2×22 = **344mm**
- Frame outer height: 400 + 2×22 = **444mm**
- Stile body height: 444mm (includes top and bottom tab protrusions: +6mm each end = 456mm total)

**Sheet fit analysis (600×600mm sheet, 2mm margin each side → 596×596 usable):**

Approximate part sizes:

| Part | W (mm) | H (mm) | Count | Notes |
|---|---|---|---|---|
| Stile (L+R) | 48 | 456 | 2 | Body 22mm + mortise protrusions each side |
| Top rail | 356 | 27 | 1 | 344mm + 6.1mm socket each end + margin |
| Bottom rail | 356 | 27 | 1 | Same |
| Crossbar (×2) | 230 | 6 | 2 | 200mm body + 15mm tenon each end... wait |

**STOP — crossbar body width for 300mm interior:**
- Body = interior width = 300mm
- Tenon each end = 15mm
- Total crossbar length = 300 + 2×15 = **330mm**

**Rail total length for 300mm interior:**
- Rail outer width = 344mm
- Plus finger socket protrusion each end: 6.1mm each → total = 344 + 2×6.1 = **356.2mm**

**Stile total height for 400mm interior:**
- Stile body = 444mm
- Tab protrusion each end: 6mm each → total = 444 + 2×6 = **456mm**

**456mm stile in a 600mm sheet: 600 − 456 = 144mm remaining height.**

Rail is 27mm tall. Two rails = 54mm. Remaining after rails: 144 − 54 = 90mm.
That's very tight but potentially feasible. Let me try a nesting layout:

**Proposed layout (portrait, 600mm wide × 600mm tall):**

```
Y=0 to 2: margin
Y=2 to 8: Crossbar 1 (330mm wide × 6mm tall) — placed horizontally
Y=10 to 16: Crossbar 2 (same)
Y=18 to 45: Top rail (356mm wide × 27mm tall)
Y=47 to 74: Bottom rail (same)
Y=76 to 532: Stile-L and Stile-R side by side (each 48mm wide × 456mm tall)
           x: 2–50 (Stile-L), 52–100 (Stile-R)
Y=76 to 118: Beater (210mm wide × 42mm tall) — placed right of stiles, x=102–312
Y=76 to 104: Shuttle 1 (180mm wide × 28mm tall) — x=314–494
Y=106 to 134: Shuttle 2 (same) — x=314–494
Y=120 to 140: Heddle bar (220mm wide × 20mm tall) — x=102–322
Y=142 to 162: Prop-L (22mm wide × 150mm tall... rotated 90°: 150mm wide × 22mm tall)
Y=164 to 184: Prop-R (same)
Y=532 to 598: Remaining space — SPARE (66mm)
```

**Check: Stile bottom = Y=532. Rail bottom = Y=74. Gap between rail bottom and stile top = 76−74 = 2mm margin. OK.**

**Check: Crossbars at Y=2–16: two crossbars = 14mm used. Rails at Y=18–74: 56mm. Stiles at Y=76–532: 456mm. Total = 532mm < 600mm ✓**

**Check: Crossbars 330mm wide. Rails 356mm wide. Both fit in 596mm usable width ✓**

**Right-side space (x=102 to 596, y=76 to 532):**
- Width available: 494mm
- Height available: 456mm
- Beater: 210×42mm ✓
- 2× Shuttle: 180×28mm each ✓
- Heddle bar: 220×20mm ✓
- Props (rotated): 150×22mm each ✓

**VERDICT: 300×400mm interior FITS on 600×600mm sheet. Tight but achievable.**

**Open sub-question:** If 300×400 is tight, should we offer 250×350mm as a fallback? Check: stile = 394+12=406mm, plenty of room. But user said 300×400 — proceed with that.

**Default parameters:**
```
INTERIOR_W = 300mm
INTERIOR_H = 400mm
STILE_W    = 22mm
RAIL_W     = 22mm
MAT        = 6mm
```

---

## Q2 — Intermediate Crossbar Type (ANSWERED)

**User answer:** Defer to conventional wisdom.

**Conventional wisdom:** Intermediate crossbars (stretchers/braces) are structural-only. They prevent the frame from bowing inward under warp tension. Warp threads are tied only to top and bottom rails. No notches on crossbars.

**DECISION:** Two structural crossbars, no notches, mortise-and-tenon into inner stile face.

**Position (300×400mm interior):**
- Interior height = 400mm
- Crossbar 1: 400/3 = 133.3mm from inner top rail face → 22 + 133 = 155mm from stile top
- Crossbar 2: 2×400/3 = 266.7mm from inner top rail face → 22 + 267 = 289mm from stile top

**Conflict check with prop mortise (Q15 — prop position TBD):**
- Crossbar 1: 151.95–158.05mm from stile top, inner face, 15mm deep
- Crossbar 2: 285.95–292.05mm from stile top, inner face, 15mm deep
- Prop mortise position to be determined in Q15

---

## Q3 / Q15 — Stand Design — SUPERSEDED BY D-23

**[SUPERSEDED 2026-03-15]** Stand design resolved as 2-piece triangular X easel. See DECISIONS.md D-22 → D-23. All analysis below is retained for audit trail only.

## Q3 / Q15 — Stand Design (UPDATED — robust, flat-pack)

**User answer:** Robust, easy assembly, flat-pack to box. No hardware preference.

**Revised analysis for 444mm tall frame:**

The frame is tall and will carry significant warp tension. Fixed-angle press-fit props (old design) work but the foot can slip. Options:

| Option | Description | Robustness | Flat-pack | Ease |
|---|---|---|---|---|
| A | Fixed-angle prop arms (old spec) | Medium — foot can slip | ✓ | ✓ |
| B (PROPOSED) | A-frame easel stand: two legs joined by a spreader bar, loom rests in notches on stand | High — spreader prevents splaying, gravity holds loom | ✓ — disassembles | Simple |
| C | Wedge-notch ladder: a separate H-frame with multiple height/angle notches | High, adjustable | ✓ | Medium |
| D | Integral folding leg (hinge via kerf) | Low on 6mm ply | ✓ | Simple |

**Proposed: Option B — A-frame stand.**

- Two legs, each ~300mm long, bevelled foot
- A crossbar (spreader) connects the two legs at ~2/3 height via a mortise or notch
- Frame sits in two notches near the top of the A-frame legs
- Stand angle: 65° (25° from vertical)
- The loom frame is not mechanically connected to the stand — it rests by gravity and warp tension
- All three stand pieces (2 legs + 1 spreader) fold flat and fit in the box

**Does the A-frame fit on the loom sheet?**
- Leg: ~300mm long × 22mm wide × 6mm thick
- Two legs + spreader: three pieces, each ~300×22mm
- Spreader: ~180mm × 22mm (span between legs when at 65°)
- These can be nested in the remaining sheet space alongside shuttles and beater

**A-frame geometry at 65°:**
- Leg length: 300mm
- Foot spread from loom base: cos(25°) × 300 = 272mm — each leg foot is 272mm back from loom base
- Notch for loom resting: near top of leg, at a height matching loom back edge
- Spreader length: distance between two leg positions (match stile outer faces: 344mm outer width → spreader ≈ 344mm but...spreader is between the two A-legs, not the stile faces)

**ISSUE:** The spreader length depends on the foot spread geometry. Need to define whether the stand straddles the frame (A-frame wider than frame) or sits under the frame (narrower). Straddling is more stable but larger. Sitting under: legs at stile faces (344mm apart), spreader = 344mm.

**ALTERNATIVE — Simpler robust stand: notched prop with toe-bar:**

Two prop arms with a horizontal toe-bar connecting their feet. The toe-bar prevents sliding. The three-piece assembly (Prop-L, Prop-R, toe-bar) presses together and flat-packs. This is simpler than an A-frame and requires less sheet space.

Toe-bar: ~380mm long (span between outer prop feet), 22mm wide, 6mm thick. Notches at each end accept the prop foot stub. The whole stand (3 pieces) assembles in 10 seconds.

**PROPOSED FINAL STAND DESIGN: notched prop pair + toe-bar.**

Parts: Prop-L, Prop-R (mirror), Toe-bar (1 piece).
Assembly: press Prop-L and Prop-R into stile outer-face mortises, slot toe-bar notches over prop feet.

Prop foot geometry:
- Prop leans at 25° from vertical when deployed
- Foot is cut square (not bevelled) — the toe-bar holds the angle
- Toe-bar sits on the table and prevents sliding

**QUESTION FOR USER:** A-frame stand (separate from loom, loom rests in notches) vs notched prop + toe-bar (attached to loom stiles, foot locked by bar)? Both flat-pack. A-frame is more stable for the taller frame. Prop+toe-bar is simpler and uses less sheet space.

---

## Q4 — Warp Notch Pitch and Count — SUPERSEDED BY D-24

**[SUPERSEDED 2026-03-15]** Pitch changed to 5mm, count to 61. See DECISIONS.md D-24. Analysis below is retained for audit trail only.

## Q4 — Warp Notch Pitch and Count (UPDATED for 300×400mm)

**Warp span = 300mm interior.**

With 10mm pitch: 300/10 = 30 gaps = **31 notches**.
Centrelines: 22, 32, 42, …, 322mm from rail outer edge (i.e., 22 + 30×10 = 322mm).
Inner stile face at 22mm, inner stile face on far side at 22+300=322mm. ✓

**Invariant check:** (31−1) × 10 = 300 = INTERIOR_W ✓

**Note:** DEF-001 from old spec (200mm interior) is resolved for the new 300mm interior: 31 notches, 10mm pitch, centrelines at 22 to 322mm.

**Status:** PROPOSED — 31 notches, 10mm pitch

---

## Q5 — Heddle Bar (for 300mm interior)

**Flat bar dimensions (revised):**
- Length: ~320mm (span between outer stile faces = 344mm; bar slightly shorter to avoid overhang) → 320mm
- Width: 20mm
- Thickness: 6mm (cut from loom sheet)
- Heddle holes: spaced at 10mm intervals (matching warp pitch), starting at 22mm from bar end → 31 holes, r=3.5mm

**Mounting:** Two U-notches cut into the top rail inner face, 20mm wide × 10mm deep, positioned near dowel hole locations in old spec (adjusted for 300mm frame). Bar drops into notches and can be lifted out.

**Notch positions on top rail inner face:**
- Must not conflict with warp notches (which are also on inner face but on a different edge — warp notches on bottom edge of top rail; heddle bar notches on inner face)
- Actually: the top rail is a 344×22mm rectangle. Warp notches are cut into the lower edge (opening downward into weaving interior). The heddle bar mounting notches are on a different face (the face perpendicular to the sheet, toward the interior) — these are actually holes/slots through the rail thickness, not edge notches.

**REVISED HEDDLE BAR MOUNTING:** Two holes (r=4mm, matching 8mm dowel diameter) through the top rail. The laser-cut heddle bar rests on pins inserted through these holes, or the bar has matching holes and pins through the holes hold it. Simpler: the heddle bar itself rests on two notched pegs, or just hangs from two loops of string through the top rail holes.

**SIMPLEST VIABLE OPTION:** Keep the two holes in the top rail (same as old spec, shifted for 300mm frame). The heddle bar (flat laser-cut piece) rests across the top of the frame, and string heddles loop around the bar and under alternate warp threads. The bar doesn't need to slot into the rail at all.

**Proposed heddle bar mounting: bar rests freely across frame top, held by warp string tension. No mounting hardware.**

---

## Q6 — Shuttle Count (for 300mm interior)

Two shuttles. Length 180mm (unchanged — appropriate for 300mm warp). ✓

---

## Q7 — Beater Span (for 300mm interior)

Beater = 310mm (frame outer width 344mm is too wide to clear stile notches; beater should span the interior plus ~5mm each side = 300+10 = 310mm).

Teeth at 10mm pitch, starting 5mm from beater edge: tooth centrelines at 5, 15, 25, …, 305mm = 31 teeth.
Aligns with warp at pitch = 10mm ✓

Handle height: 22mm. Tooth height: 20mm. Tooth width: 4mm. Gap: 6mm. Total beater height: 42mm.

---

## Q11 — 3D Mortise Conflict Check (UPDATED for 300×400mm)

**Stile body height = 444mm.**
**Prop pivot (assume same: 150mm from stile bottom) = 444−150 = 294mm from stile top.**

| Mortise | Centre from stile top (mm) | Height span (mm) | Face | Depth (mm) |
|---|---|---|---|---|
| Top socket | 3 (tab zone) | 0–6 | end | full |
| Crossbar 1 | 155 | 151.95–158.05 | inner | 15 |
| Crossbar 2 | 289 | 285.95–292.05 | inner | 15 |
| Prop | 294 | 290.95–297.05 | outer | 11 |

**CONFLICT: Crossbar 2 (285.95–292.05) and Prop (290.95–297.05) overlap at 290.95–292.05mm (1.1mm overlap).**

At the overlap: Crossbar mortise depth = 15mm (inner face) + Prop mortise depth = 11mm (outer face) = 26mm > 22mm stile width.

**DEF-005: Crossbar 2 mortise and Prop mortise intersect in 3D for 300×400mm frame with prop pivot at 150mm from stile bottom.**

**Fix options:**
1. Move prop pivot higher: 444−200=244mm from top → prop at 200mm from bottom. Then prop centre = 244mm, span = 240.95–247.05mm. No overlap with crossbar 2 (285–292). ✓
2. Move crossbar 2 lower: to 2/3 × 400 = 266.7mm from inner top rail face = 22+267=289mm from stile top → same issue. Could move to 310mm from stile top = 288mm from stile bottom. Still potentially conflicts.
3. Move prop pivot to 160mm from stile bottom: centre = 444−160=284mm from stile top, span=280.95–287.05mm. Crossbar 2 at 285.95–292.05. Still 1mm overlap.
4. Move crossbar 2 to 3/5 height instead of 2/3: 3×400/5=240mm from inner top → 22+240=262mm from stile top. Span=258.95–265.05mm. No conflict with prop at 290mm from top. ✓ But then crossbar spacing is asymmetric (at 1/3 and 3/5 instead of 1/3 and 2/3).
5. Keep crossbars at 1/3 and 2/3, move prop lower: prop at 120mm from stile bottom = 444−120=324mm from stile top. Span=320.95–327.05mm. No overlap with crossbar 2 (285–292). ✓

**Preferred fix: Move prop pivot to 120mm from stile bottom (instead of 150mm).**

Geometry check at new prop position:
- Pivot height above table (at 65° lean): sin(65°)×120 = 108.8mm ≈ 109mm
- Table footprint: cos(25°)×150 → now cos(25°)×prop_arm_length. Prop arm length stays 150mm.
- Foot-to-frame-base horizontal distance: This depends on prop arm length, not pivot height. Still ≈ 135mm footprint.
- No conflict with crossbar 2 ✓

**Re-check all pairs:**

| Mortise | Centre from stile top (mm) | Height span (mm) | Face | Depth (mm) |
|---|---|---|---|---|
| Crossbar 1 | 155 | 151.95–158.05 | inner | 15 |
| Crossbar 2 | 289 | 285.95–292.05 | inner | 15 |
| Prop | 324 | 320.95–327.05 | outer | 11 |

- CB1 vs CB2: 151–158 vs 285–292 → no overlap ✓
- CB1 vs Prop: 151–158 vs 320–327 → no overlap ✓
- CB2 vs Prop: 285–292 vs 320–327 → no overlap ✓
- CB1 vs CB2 (same face, inner): no height overlap → no conflict ✓

**DEF-005 resolved by moving prop pivot to 120mm from stile bottom.** ✓

---

## Q14 — Sheet Fit for 300×400mm Interior (UPDATED)

See Q1 analysis. **VERDICT: FITS**, but requires careful nesting. Nesting plan to be finalized in implementation.

---

## Q15 — Stand Design for 444mm Tall Frame — SUPERSEDED BY D-23

**[SUPERSEDED 2026-03-15]** See DECISIONS.md D-23. Stand is 2-piece triangular X easel, 6mm ply, output/optional_loom_stand.svg.

---

## Sparring Topics

1. **DEF-005 resolved:** Crossbar 2 vs Prop conflict fixed by moving prop to 120mm from stile bottom. To be confirmed.

2. **Stand design (Q15):** Two options presented above — need user decision.

3. **Warp notch count (31):** Odd vs even. 31 notches gives a centre notch with equal count either side (15+1+15). Clean for symmetric warping. ✓

4. **Box interior for 300×400mm loom:**
   - Longest part: stile = 456mm → box interior length ≥ 456mm
   - Box on 600×600mm sheet: interior 460×330mm would fit the parts. Box outer = 466×336mm.
   - But a 466×336mm box needs walls. Long wall with dado slot: ~480mm parts. Fits on 600mm sheet.
   - Stacked depth: 2 rails (22mm each) + 2 stiles (22mm each) + 2 crossbars (6mm each) + 2 props (6mm each) + 2 shuttles (28mm each, stacked) + beater (42mm) + heddle bar (20mm) = 44+44+12+12+56+42+20 = **230mm** — far too deep for a box.
   - **PROBLEM: Box interior depth of 230mm is not feasible from a 3mm ply sheet cut into box walls.**
   - Parts must be **nested flat**, not stacked. The box is a flat box (like a picture frame box), not a deep box.
   - Revised: parts all lie flat in the box interior. Max thickness of any part = 22mm (stile, laid on its flat face). Box interior height = 22mm + clearance = 25mm.
   - **Box interior: 460mm × 330mm × 25mm.** Long walls: 460mm × 25mm. Short walls: 330mm × 25mm.
   - This fits on 600×600mm 3mm ply sheet with the lid. ✓

5. **Beater tooth count and alignment:** 31 teeth at 10mm pitch starting 5mm from beater edge — confirmed above. But should the teeth be at exactly the warp notch positions when the beater is centred over the frame? Centreline alignment: beater centre = 155mm from beater edge. Frame interior centre = 150mm from inner stile face. If beater overhangs 5mm each side, then beater edge to inner stile face = 5mm, and beater teeth start at 5mm from beater edge = 0mm from inner stile face = first warp notch. ✓
