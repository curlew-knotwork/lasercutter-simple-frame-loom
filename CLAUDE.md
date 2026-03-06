# Project: laser-cut frame loom

## SESSION START — READ THESE IN ORDER
1. `docs/FAILURE_PATTERN_REGISTRY.md` — run the full pattern scan (#P-G1 through #P-Q4) before touching any file
2. `docs/DECISIONS.md` — all locked decisions (D-01 through D-12); AUTHORITY over everything else
3. `docs/FAILURE_REGISTRY.md` — known defects; don't repeat them

## KEY FACTS

**Three SVG outputs:**
- `output/loom.svg` — 6mm birch ply, 600×600mm, all loom parts
- `output/box.svg` — 3mm birch ply, 600×600mm, box panels + A-frame stand
- `output/test_cut.svg` — 3mm scrap, calibration/fit test (not yet written)

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

## JOINT GEOMETRY (D-01, D-04, D-07)
- N=1 finger joint: TAB_W = STILE_W/3 = 7.33mm > MAT=6mm ✓
- SOCK_W = TAB_W + 0.10mm clearance (kerf already in SOCK_W)
- Crossbar mortises: 15mm deep, 6.1mm wide, inner face only, no 3D intersection
- Stand mortises: 15mm deep, 3.1mm wide through stile broad face (rect_hole)

## KNOWN FAILURE MODES (from FAILURE_REGISTRY.md)
- Mortise direction: concave (INTO body), never convex (OUT of body). Check: `max(xs) ≤ STILE_W`
- Regex `d="..."` matches `id=` first. Use `' d="..."'` (with leading space).
- SVG preamble is `<?xml...><svg...>`, not `<svg...>`. Use `"<svg " in svg`.

## STAGE STATUS
- Stages 0–5 complete: sparring, proofs, params, geometry, loom.py, box.py (basic)
- 171 tests passing
- **Open design questions** (surface before touching code):
  - D-07 REVISION CANDIDATE: crossbar through-hole (stile broad face) vs. open edge mortise
  - Box assembly: butt-joint walls need finger joints or labelling as glue-only
  - Stand: assembly fit and function not yet verified by eye
