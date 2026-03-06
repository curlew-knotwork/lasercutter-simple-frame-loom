# Failure Registry
**Format:** one entry per defect/failure instance, newest last.
**Use:** update whenever a defect is found, fixed, or its root cause identified.

Each entry answers: what failed, which pattern it maps to, root cause, what check would have caught it EARLIER.

---

## Status of design-phase defects (from old DEFECTS.md)

| ID | Description | Severity | Status |
|---|---|---|---|
| DEF-001 | Old spec: 20 notches × 10mm pitch → span 190mm ≠ 200mm interior | Medium | CLOSED — new design: 31 notches × 10mm = 300mm = INTERIOR_W ✓ |
| DEF-002 | Old spec: stretcher+prop mortises overlap 3D (26mm > 22mm stile width) | Critical | CLOSED — D-08: no prop mortises; stand is independent A-frame |
| DEF-003 | v6 SVG comment says N=2 (4.4mm < MAT=6mm) — wrong | Low | CLOSED — no hand-coded SVG; code generates everything |
| DEF-004 | Old .svg V11.0 does not match SPECIFICATION_LOCK.md (different design) | Medium | CLOSED — old files archived in docs/archive/ |
| DEF-005 | 300×400mm: crossbar2 vs prop mortise overlap (26mm > 22mm) | Critical | CLOSED — D-08: same fix as DEF-002 |

---

## F-001 — Warp notch count/pitch inconsistency
- **Found:** Session 1, during sparring on old spec
- **Stage found:** Specification (pre-code)
- **Pattern:** #P-G2 (count/pitch/span invariant violated)
- **Symptom:** Old spec said 20 notches × 10mm pitch → span = 190mm ≠ 200mm interior
- **Root cause:** Spec authored by arithmetic rather than invariant. No constraint enforced.
- **Fix:** New design uses 31 notches × 10mm pitch → (31-1)×10 = 300 = INTERIOR_W ✓; invariant written in `proofs/invariants.py::inv_notch_count_pitch_span`
- **Earlier catch:** Writing the invariant predicate BEFORE spec lock would have rejected the 20-notch spec on first check.
- **Linked:** DEF-001, DECISIONS.md D-06

## F-002 — Mortise 3D intersection in old spec
- **Found:** Session 1, during sparring on old spec
- **Stage found:** Specification (pre-code)
- **Pattern:** #P-G1 (mortise 3D intersection)
- **Symptom:** Old spec: stretcher mortise (147mm, inner, 15mm deep) + prop mortise (144mm, outer, 11mm deep). 15+11=26mm > stile_w=22mm → stiles would be hollow.
- **Root cause:** Mortises placed independently on each face without checking combined depth < member width.
- **Fix:** Eliminated prop mortises entirely (D-08); stand is independent A-frame. Invariant written in `proofs/invariants.py::inv_no_mortise_3d_intersection`.
- **Earlier catch:** invariant `inv_no_mortise_3d_intersection` in params.py would have raised immediately.
- **Linked:** DEF-002, DEF-005, DECISIONS.md D-08

## F-003 — Mortise direction wrong (convex vs concave)
- **Found:** Session 1, during geometry.py implementation
- **Stage found:** Code (geometry.py `stile_pts`)
- **Pattern:** #P-C1 (sign/direction error)
- **Symptom:** Mortises implemented as CONVEX (x > STILE_W), protruding outward. bbox xmax=37mm instead of 22mm. Stile would not be a single flat piece; mortise would protrude into frame interior.
- **Root cause:** Misread "mortise on inner face" as "protrudes from inner face" rather than "slot going INTO the body from the inner face".
- **Fix:** Made mortise CONCAVE: inner face steps LEFT from x=stile_w to x=stile_w−mort_d. Test `test_mortise_is_concave_not_convex` catches regressions.
- **Earlier catch:** Writing test for concavity (x ≤ STILE_W for all points) BEFORE coding would have caught this immediately.
- **Linked:** DEF-004 (old SVG had wrong geometry)

## F-004 — SVG path d-attribute regex matched id= not d=
- **Found:** Session 2, test_loom.py initial run
- **Stage found:** Test code (test_loom.py)
- **Pattern:** #P-T1 (test assertion wrong / not testing what it claims)
- **Symptom:** `re.search(r'd="([^"]+)"', path)` matched `id="crossbar_1_outer"` (the `d` in `id` suffix) instead of the path `d` attribute. Group 1 = `"crossbar_1_outer"`, which does not end with `Z`.
- **Root cause:** Regex ambiguity: `d="` appears in `id="..."` too. No word-boundary assertion.
- **Fix:** Changed regex to `r' d="([^"]+)"'` (leading space) to require a non-attribute-name character before `d=`.
- **Earlier catch:** Checking the matched group value in a print statement before asserting.

## F-005 — SVG starts with <?xml?> not <svg>
- **Found:** Session 2, test_loom.py initial run
- **Stage found:** Test code (test_loom.py)
- **Pattern:** #P-T1 (test assertion wrong / not testing what it claims)
- **Symptom:** `svg.lstrip().startswith("<svg")` failed because SVG includes XML declaration preamble.
- **Root cause:** Assumed SVG output format without verifying what `svg_open()` actually emits.
- **Fix:** Changed assertion to `"<svg " in svg`.
- **Earlier catch:** Read `svg_open()` implementation before writing the test.
