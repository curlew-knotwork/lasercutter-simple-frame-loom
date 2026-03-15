# Failure Pattern Registry
**Version:** 1
**Scope:** All stages — spec, proofs, code, tests, SVG output.

Run the full pattern scan (#P-G1 through #P-Q4) at:
- Start of each session (before touching any file)
- After every src/ edit (before commit)
- After every SVG generation (before presenting to user)

Any YES: surface it immediately. Do not proceed until addressed.

---

## Category G — Geometric Invariants

| ID | Pattern | Trigger Question | Check Method |
|---|---|---|---|
| P-G1 | Mortise 3D intersection | Do any two mortises on the same member overlap in depth? | For all mortise pairs on same member: if y-ranges overlap, sum of depths < member width |
| P-G2 | Count/pitch/span mismatch | Does (count−1)×pitch == span? | `inv_notch_count_pitch_span(p)` — predicate must return True |
| P-G3 | Part out of sheet bounds | Does any part (+ margin) exceed 600×600mm? | `inv_critical_parts_fit_sheet(p)` + bounding box of every placed part |
| P-G4 | Part overlap on sheet | Do any two parts share sheet area? | For all pairs: `bboxes_overlap(a.bbox, b.bbox)` must be False |
| P-G5 | Tab too narrow | Is any finger tab narrower than the material? | `inv_tab_wider_than_mat(p)` — tab_w > MAT |
| P-G6 | Clearance out of range | Is socket-to-tab clearance outside [0.05, 0.40]mm? | `inv_clearance_in_range(p)` — 0.05 ≤ SOCK_W−TAB_W ≤ 0.40 |
| P-G7 | Mortise in corner zone | Does any crossbar mortise enter the finger-joint corner zone? | `inv_crossbar_mortises_clear_corner_zone(p)` |
| P-G8 | Box interior undersized | Does any loom part fail to fit inside the box? | `inv_box_interior_holds_loom(p)` |
| P-G9 | Notch depth >= rail width | Would any notch cut entirely through the rail? | NOTCH_D < RAIL_W (checked by `inv_notch_depth_less_than_rail`) |
| P-G10 | Open path / unclosed Z | Does any cut path not end with Z? | `re.findall(r' d="([^"]+)"', svg)` — all must end with Z |

---

## Category C — Code Errors

| ID | Pattern | Trigger Question | Check Method |
|---|---|---|---|
| P-C1 | Sign / direction error | Is any direction (inward/outward, up/down, left/right) reversed? | Trace formula at boundary: check min/max of pts match expected bbox |
| P-C2 | Off-by-one in count | Is any count off by ±1? | Verify count formula: count = int(round(span/pitch)) + 1 |
| P-C3 | Local vs sheet coords confused | Are local-coord pts placed directly on sheet without `place()`? | Always use `place()` for all sheet positions |
| P-C4 | Hole direction wrong | Are hole outlines CW instead of CCW (or vice versa)? | Holes must use CCW path so fill:evenodd cuts them out |
| P-C5 | Formula derived from symptoms | Was a constant chosen to make a test pass rather than from spec? | Every constant in params.py has a named reference (D-XX comment) |
| P-C6 | Ambiguous regex matches wrong element | Does a regex match a different attribute than intended? | Use leading/trailing delimiters (space, quote) not just `attrname=` |

---

## Category T — Test Failures

| ID | Pattern | Trigger Question | Check Method |
|---|---|---|---|
| P-T1 | Test asserts wrong thing | Does the test actually exercise the claim in its docstring? | Read the assertion: what concrete value is checked vs what is claimed |
| P-T2 | Missing unhappy-path test | Is there a test that verifies the error for every invariant? | For each invariant function: one test must confirm it FAILS for a bad input |
| P-T3 | Proof-first gate skipped | Was src/ modified before a failing test existed? | Check git log: failing test commit must precede src/ edit commit |
| P-T4 | Test imports wrong module | Does the test import the module it claims to test? | Read the import block of every test file |
| P-T5 | Verify script not called | Does the verify script import and call the changed module? | Read verify_*.py imports |

---

## Category S — Spec / Design Failures

| ID | Pattern | Trigger Question | Check Method |
|---|---|---|---|
| P-S1 | Invariant written after fact | Was an invariant derived from the code rather than from the spec? | Every invariant in `proofs/invariants.py` must have a corresponding DECISIONS.md entry |
| P-S2 | Silent architectural choice | Was a design question resolved in code without surfacing it? | Before every src/ edit: name any architectural choice being made |
| P-S3 | Spec parameter not locked | Is any base parameter (interior_w, mat, kerf) floating between sessions? | DECISIONS.md must list every base parameter with rationale |
| P-S4 | Missing mating-pair check | Is any joint (tab+socket, tenon+mortise) without a matching invariant? | List all joint types; check each has a clearance invariant |

---

## Category Q — Output Quality

| ID | Pattern | Trigger Question | Check Method |
|---|---|---|---|
| P-Q1 | SVG/spec mismatch | Does any SVG coordinate differ from the computed params value? | Parse SVG bounding boxes; compare to params values numerically |
| P-Q2 | Cut/etch confusion | Does any label or reference line use the cut stroke? | All text/etch → #000000 0.4mm; all cuts → #ff0000 0.1mm (preview) |
| P-Q3 | Artifact in /tmp not copied | Was a generated file written to /tmp and not moved? | Check write() output path — must be in project output/ dir |
| P-Q4 | Output presented without verification | Was an SVG described to user before verify() confirmed it passes? | Always: generate → verify() → report failures or "ALL PASS" → present path |

---

## Session Scan Log

| Date | Task | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | G10 | C1 | C2 | C3 | C4 | C5 | C6 | T1 | T2 | T3 | T4 | T5 | S1 | S2 | S3 | S4 | Q1 | Q2 | Q3 | Q4 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-06 | Stage 0 — sparring | YES | YES | — | — | YES | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | All in OLD spec; new design eliminates them |
| 2026-03-06 | Stage 1–5 — proofs→loom.py→tests | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | YES(F-003) | NO | NO | NO | NO | NO | YES(F-004,F-005) | NO | YES* | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | *T3: test_loom.py written after loom.py (not before) |
| 2026-03-07 | Session recheck — D-19 + MD rewrites committed | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | 285 tests pass; all 3 generators ALL PASS; D-10 not marked superseded (doc only, no code impact) |
| 2026-03-15 | D-23 tab direction + 2-piece fix | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | YES | NO | NO | NO | NO | NO | YES | P-C1: ledge hung off corner point with no material support (mechanically incoherent). P-S2: silently generated two different cut functions instead of surfacing "should these be identical pieces?". P-Q4: committed without user review. |

---

## Pattern Occurrence Counts

*(Updated after each scan. Watch for trends — any count increasing → add a pre-commit check.)*

| Pattern | Count | Last Seen |
|---|---|---|
| P-G1 Mortise 3D intersection | 1 | F-002 (old spec) |
| P-G2 Count/pitch/span | 1 | F-001 (old spec) |
| P-G3 Part OOB | 0 | — |
| P-G4 Part overlap | 0 | — |
| P-G5 Tab too narrow | 1 | old spec N=2 comment |
| P-G6 Clearance OOR | 0 | — |
| P-G7 Mortise in corner zone | 0 | — |
| P-G8 Box undersized | 0 | — |
| P-G9 Notch depth | 0 | — |
| P-G10 Open path | 0 | — |
| P-C1 Sign/direction | 2 | 2026-03-15 (ledge at corner, no material support) |
| P-C2 Off-by-one | 0 | — |
| P-C3 Coord confusion | 0 | — |
| P-C4 Hole direction | 0 | — |
| P-C5 Formula from symptom | 0 | — |
| P-C6 Regex ambiguity | 1 | F-004 (test regex) |
| P-T1 Test asserts wrong | 2 | F-004, F-005 |
| P-T2 Missing unhappy path | 0 | — |
| P-T3 Proof-first skipped | 1 | test_loom.py after loom.py |
| P-T4 Wrong import | 0 | — |
| P-T5 Verify not called | 0 | — |
| P-S1 Invariant after fact | 0 | — |
| P-S2 Silent arch choice | 1 | 2026-03-15 (two different cut functions vs. one identical piece) |
| P-S3 Param not locked | 0 | — |
| P-S4 Missing mating pair | 0 | — |
| P-Q1 SVG/spec mismatch | 0 | — |
| P-Q2 Cut/etch confusion | 0 | — |
| P-Q3 Artifact in /tmp | 0 | — |
| P-Q4 Unverified output | 1 | 2026-03-15 (committed stand SVG without user review) |

---

## Enforcement Rules (per stage)

Rules marked **[WRITTEN OUTPUT REQUIRED]** must produce text in the response before proceeding. Unwritten = not checked.

### Spec / Sparring stage
- Before locking any parameter: run P-G1 through P-G9 against the parameter set. **[WRITTEN OUTPUT REQUIRED]**: list each check as "P-Gn: NO — reason" or "P-Gn: YES — blocker".
- Before locking any joint: name the mating pair; confirm clearance invariant exists (P-S4).

### Proof / invariant stage
- Every invariant must map to a DECISIONS.md entry (P-S1).
- Every invariant must have both a happy-path and an unhappy-path test (P-T2).

### Code stage (src/ edit)
- **[WRITTEN OUTPUT REQUIRED]** Before any new geometry: write in plain prose — where does the piece stand upright, what direction does each protrusion face, what material connects it to the body. Corner-point connection = zero structural width = STOP. (P-C1)
- **[WRITTEN OUTPUT REQUIRED]** Before any new builder function: write "Identical piece or different cut? [answer] because [reason]." No code until this is written. (P-S2)
- Failing test must exist BEFORE the first src/ edit. Name it. (P-T3)
- After writing each formula: trace at min, max, and zone-edge values with concrete numbers. (P-C1, P-C2)

### SVG generation stage
- Call `verify()` before presenting any path (P-Q4).
- Output must be in `output/`, not `/tmp` (P-Q3).
- All `' d="([^"]+)"'` matches must end with Z (P-G10).
- **[WRITTEN OUTPUT REQUIRED]** After generating: write the file path. Write "Review before commit." STOP. No commit until user confirms in a subsequent turn. (P-Q4)

### Pre-"done" check
- **[WRITTEN OUTPUT REQUIRED]** Trace 2–3 specific polygon vertices in physical standing orientation with concrete mm values. State what material connects each protrusion to the body. Bbox dimensions are not this check. (P-C1, P-Q4)

### Test writing stage
- Read the assertion: does the concrete value checked match the docstring claim? (P-T1)
- Use `' d="([^"]+)"'` not `'d="([^"]+)"'` for path attribute regex (P-C6).
- Confirm the test imports the module under test (P-T4).
