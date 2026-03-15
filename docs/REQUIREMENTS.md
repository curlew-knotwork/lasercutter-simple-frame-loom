# Requirements
**Version:** 1
**Date:** 2026-03-06
**Status:** DRAFT — awaiting answers to DESIGN.md open questions

---

## 1. User Requirements (as stated)

- Gift for a beginner-to-intermediate weaver
- Frame loom from 6mm birch plywood, 600×600mm sheet
- Frame parts: uprights (stiles), top and bottom cross-braces with warp notches, two intermediate cross-supports evenly spaced between top and bottom
- All joints: finger-press tight — no glue, no hardware required for assembly
- One SVG for loom sheet: frame, shuttle, beater, heddle bar, tilted stand/support for table use at an angle
- Separate SVG: 3mm plywood sliding-lid storage box
- Separate SVG: test/calibration cut (3mm plywood)
- Design should reflect common wisdom for beginner-intermediate frame loom use
- Should physically assemble in 3D

---

## 2. System Requirements (as stated)

1. **Four SVG outputs, one sheet each:**
   - `loom.svg` — 6mm birch plywood, 600×600mm max
   - `optional_box.svg` — 3mm birch plywood, 600×600mm max (D-17)
   - `optional_loom_stand.svg` — 6mm birch plywood, 600×600mm max (D-23)
   - `test_cut.svg` — 3mm plywood, scrap size

2. **Loom and box must assemble in 3D** — all mortises, tabs, slots must be geometrically consistent with 6mm (loom) and 3mm (box) material thickness

3. **Loom must fit inside box** — all loom parts, fully disassembled and laid flat, must fit within box interior

4. **Test coverage:**
   - Happy-path tests: every geometric invariant holds for default parameters
   - Unhappy-path tests: invalid parameters produce explicit failures, not silently bad geometry
   - Tests must run against generated SVG content, not just the generator source

5. **Proofs of correctness:**
   - All geometric invariants stated as formal predicates
   - Each predicate proven to hold for all valid parameter ranges (Dijkstra-style: no examples, just invariants)
   - Boundary conditions explicitly checked (min, max, zone edges)

6. **Parametric design:**
   - All dimensions derived from a small set of base parameters
   - Default values = most common beginner-intermediate frame loom sizes (from common wisdom)
   - Any conforming parameter set must produce a valid, cuttable, assembleable loom
   - Several random useful sizes must be generated and tested (both valid and invalid configurations)

7. **Claude does the heavy lifting:** identifies problems, proposes solutions, iterates — does not wait for user to find bugs

8. **Multi-stage project discipline:**
   - Stage 1: Sparring + requirements capture (this document)
   - Stage 2: Design decisions (DECISIONS.md) — no code until this is locked
   - Stage 3: Proofs written (PROOFS.md) — invariants stated before implementation
   - Stage 4: Tests written (failing) — before any SVG generator code
   - Stage 5: Generator implemented until tests pass
   - Stage 6: SVG artifact verification (not just exit code)
   - Stage 7: Decision record + defect record updated

9. **Persistence:** All important data, open questions, answers, specs, and decisions must be written to tracked files. Claude treats its own session memory as volatile — the documents are the truth.

10. **Repo structure and working practices** proposed by Claude (see ARCHITECTURE.md when created)

---

## 3. Interpreted / Inferred Requirements

These are not verbatim but are necessary consequences of the above:

| Inferred requirement | Source | Status |
|---|---|---|
| Warp notches on top and bottom rails only (not intermediate crossbars) | Standard frame loom design | PROPOSED — confirm |
| Intermediate crossbars are structural (anti-bow), not for warping | Common wisdom | PROPOSED — confirm |
| Intermediate crossbars connect via mortise-and-tenon (press-fit) into stile inner faces | Required for press-fit assembly without tools | PROPOSED — confirm |
| Tilted stand = fixed-angle press-fit prop arms (laser cut flat) | Only viable without hardware | PROPOSED — confirm |
| Default stand angle = 65° from horizontal (25° lean from vertical) | Ergonomic standard for table weaving | PROPOSED — confirm |
| Default interior weaving area = 200×250mm | Fits a small wall hanging; fits on 600×600 sheet with other parts | PROPOSED — see Q1 |
| Heddle bar = laser-cut flat bar with heddle holes (not a round dowel) | Fits on sheet; beginner-friendly | PROPOSED — confirm |
| 2 shuttles on loom sheet | Common wisdom for alternating wefts | PROPOSED — confirm |
| Warp notch pitch = 10mm (10 EPI) | Beginner-friendly for yarn 2–4mm | PROPOSED — see Q5 |
| All parts on loom sheet laid in landscape orientation | Sheet efficiency | ASSUMED |
| Box interior height ≥ stacked thickness of all loom parts | Loom-fits-in-box requirement | DERIVED |
| Test cut verifies: tab/socket fit, dado groove fit, lid clearance | Required before committing either full sheet | DERIVED |
| stroke-width = 0.1mm in SVG (preview); note to change to 0.01mm for laser | Epilog CorelDraw workflow | ASSUMED — confirm with user |

---

## 3b. Additional Requirements (from sparring)

| Requirement | Source |
|---|---|
| Each laser-cut piece must be a single unified closed-outline path. Internal holes are separate closed paths. No piece is a collection of overlapping rectangles. | User, 2026-03-06 |
| No mortise may overlap with any other mortise, tenon, tab, slot, or structural void on the same member in 3D. | User, 2026-03-06 |
| Every mortise-tenon pair must mate: mortise drawn width ≥ tab drawn width; net clearance 0.05–0.40mm. | User, 2026-03-06 |
| Every tab-socket pair must mate: same constraint as mortise-tenon. | User, 2026-03-06 |
| Stand (easel): separate 6mm ply sheet (output/optional_loom_stand.svg). Superseded from 3mm/box-sheet by D-16→D-23. | User, 2026-03-06; updated 2026-03-15 |
| Output is two sheets minimum (loom 6mm, box/stand 3mm) plus test cut from scrap. | Derived |

---

## 4. Out of Scope (this version)

- Rigid heddle (precision-slotted)
- Tapestry frame (no heddle mechanism)
- Hardware (screws, bolts, hinges)
- Finishing instructions (sanding, oiling)
- MDF instruction sheet (noted in old spec §17 — defer)
- Multiple sheet sizes (only 600×600 for now)

---

## 5. Open Questions

See DESIGN.md for the full question register with proposed answers.

Priority questions blocking all design work:

| ID | Question | Blocking |
|---|---|---|
| Q1 | Interior weaving area (200×250mm or larger)? | Yes — drives all dimensions |
| Q2 | Intermediate crossbars: structural-only, mortise-and-tenon from inner face? | Yes — drives stile mortise layout |
| Q3 | Prop/stand: fixed-angle press-fit or something else? | Yes — drives stile outer-face mortise |
