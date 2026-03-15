# Project: laser-cut frame loom

## SESSION START — READ THESE IN ORDER
1. `docs/FAILURE_PATTERN_REGISTRY.md` — run the full pattern scan (#P-G1 through #P-Q4) before touching any file
2. `docs/DECISIONS.md` — all locked decisions (D-01 through D-29); AUTHORITY over everything else
3. `docs/FAILURE_REGISTRY.md` — known defects; don't repeat them

## KEY FACTS

**Four SVG outputs:**
- `output/loom.svg` — 6mm birch ply, 600×600mm, all loom parts
- `output/optional_box.svg` — 3mm birch ply, 600×600mm, box panels (D-17: renamed from box.svg)
- `output/optional_loom_stand.svg` — 6mm birch ply, 600×600mm, D-23 2-piece triangular X easel
- `output/test_cut.svg` — 3mm scrap, calibration/fit test

**Interior:** 300×400mm (scarf). Frame outer: 344×444mm. Stile total height: 456mm.

**Material:** MAT=6mm (loom), MAT3=3mm (box/stand). Kerf=0.15mm/side.

**All geometry flows from `src/params.py`.** `assert_all(DEFAULT)` runs at import. Never hardcode dimensions.

## PROOF-FIRST GATE (PROJECT-SPECIFIC)
- `src/` edit → must have a failing test in `tests/` first
- `geometry.py` new function → test in `tests/test_geometry.py`
- `loom.py` / `box.py` change → test in `tests/test_loom.py` or `tests/test_box.py`
- After EVERY src/ edit: run `.venv/bin/python3 -m pytest tests/ -q` — must stay green

## SVG CONVENTIONS
- Stroke: `#ff0000`, width `0.1mm` (preview); change to `0.01mm` for actual laser use
- Fill: `none` on all cut paths
- All cut paths: closed (end with `Z`)
- Labels/text: `#000000`, `0.4mm` (etch, not cut)
- Holes (circles, ellipses, rects): separate closed paths inside outer boundary
- Path regex for closed-check: `' d="([^"]+)"'` (note leading space — avoids matching `id=`)

## JOINT GEOMETRY (D-01, D-04, D-13)
- N=1 finger joint: TAB_W = STILE_W/3 = 7.33mm > MAT=6mm ✓
- SOCK_W = TAB_W + 0.10mm clearance (kerf already in SOCK_W)
- Crossbar mortises: 5mm deep, 20.1mm wide, inner face only (closed rect-hole; D-13)
- Stand (D-23): right-triangle pieces, cross-halving at L/2, slot_d=W/4=20mm, foot tab from hypotenuse

## HARD GATES — EXECUTE THESE, DO NOT READ AND SKIP

### Before writing any polygon or geometry (P-C1, P-S2)
1. Write in plain prose: where does the piece stand, what direction does each protrusion face, what material is behind it. If a protrusion connects only at a corner vertex: STOP, redesign.
2. Write explicitly: "Identical piece or different cut? [answer] because [reason]." No implicit decisions.

### Before any src/ edit (P-T3)
3. Name the failing test that exists. No test named = do not edit src/.

### After generating any SVG (P-Q4)
4. Write the file path. Write "Review before commit." STOP. Do not commit in the same turn. Commit only after user confirms in the next turn.

### Before any "done" claim (P-C1, P-Q4)
5. Trace 2–3 specific polygon vertices in physical standing orientation with concrete mm values. State what material connects each protrusion to the body. "bbox=450×110mm" is not this check.

## KNOWN FAILURE MODES (from FAILURE_REGISTRY.md)
- Mortise direction: concave (INTO body), never convex (OUT of body). Check: `max(xs) ≤ STILE_W`
- Regex `d="..."` matches `id=` first. Use `' d="..."'` (with leading space).
- SVG preamble is `<?xml...><svg...>`, not `<svg...>`. Use `"<svg " in svg`.

## STAGE STATUS
- Stages 0–10 complete: sparring, proofs, params, geometry, loom.py, box.py, stand.py (D-23), test_cut.py, generate.py, parametric tests
- 340 tests passing
