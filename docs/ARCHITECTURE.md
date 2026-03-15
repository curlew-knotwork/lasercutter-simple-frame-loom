# Architecture
**Version:** 2
**Date:** 2026-03-15
**Status:** CURRENT — stages 0–6 complete, 340 tests passing

---

## Repo Structure

```
lasercutter-simple-frame-loom/
│
├── REQUIREMENTS.md          # user + system requirements
├── DECISIONS.md             # locked design decisions (authority)
├── DESIGN.md                # sparring, open questions, proposals (audit trail)
├── FAILURE_REGISTRY.md      # defect log + corrections
├── FAILURE_PATTERN_REGISTRY.md  # exit-gate pattern scan log
├── ARCHITECTURE.md          # this file
│
├── src/
│   ├── params.py            # ALL constants derived from base parameters; invariant checks
│   ├── geometry.py          # shared geometric primitives (path builder, polygon ops)
│   ├── loom.py              # loom SVG generator (imports params, geometry)
│   ├── box.py               # box SVG generator
│   ├── stand.py             # stand SVG generator (D-23: 2-piece triangular X easel)
│   ├── generate.py          # CLI: python -m src.generate --width W --height H --pitch P
│   └── test_cut.py          # calibration/fit-test cut generator
│
├── proofs/
│   ├── invariants.py        # formal invariant predicates (pure functions, no side effects)
│   ├── verify_loom.py       # runs all loom invariants against generated SVG
│   ├── verify_box.py        # runs all box invariants against generated SVG
│   └── verify_assembly.py   # cross-checks: loom fits in box, joints mate, no overlaps
│
├── tests/
│   ├── test_params.py       # invariant checks for default params (happy path)
│   ├── test_loom.py         # loom geometry tests (happy + unhappy)
│   ├── test_box.py          # box geometry tests
│   ├── test_stand.py        # stand geometry tests
│   └── test_parametric.py   # random valid + invalid sizes; confirm correct pass/fail
│
├── output/                  # generated SVGs — never hand-edited
│   ├── loom.svg
│   ├── optional_box.svg     # D-17: renamed from box.svg
│   ├── optional_loom_stand.svg  # D-16+: separate optional sheet
│   └── test_cut.svg
│
└── docs/archive/            # old hand-made files, not used
    ├── lasercutter-simple-frame-loom.svg   # V11.0 Ironman — superseded
    └── lasercutter-simple-frame-loom       # v6 draft — superseded
```

---

## Module Responsibilities

### `src/params.py`

Single source of truth for all constants. Structure:

```python
# Base parameters (user-configurable)
INTERIOR_W   = 300.0   # mm, weaving interior width
INTERIOR_H   = 400.0   # mm, weaving interior height
MAT          = 6.0     # mm, loom material thickness (nominal)
MAT3         = 3.0     # mm, box/stand material thickness (nominal)
SHEET_W      = 600.0   # mm
SHEET_H      = 600.0   # mm
KERF         = 0.15    # mm per cut side
MARGIN       = 2.0     # mm, minimum clearance between parts and sheet edge

# Derived constants (computed, not manually set)
STILE_W      = 22.0    # mm, stile/rail width (fixed by finger joint analysis)
RAIL_W       = STILE_W
TAB_W        = STILE_W / 3          # finger joint tab (N=1): 7.333mm
SOCK_W       = TAB_W + 0.1          # socket: 7.433mm (0.1mm clearance)
TAB_L        = MAT                   # finger joint tab length = material thickness
...

# Invariant checks (run at import time — fail fast)
assert (NOTCH_COUNT - 1) * NOTCH_PITCH == INTERIOR_W, "Notch invariant violated"
assert TAB_W > MAT, "Tab too narrow"
assert SOCK_W - TAB_W >= 0.05, "Clearance too small"
...
```

### `src/geometry.py`

Pure geometric functions:
- `rect(x, y, w, h)` → closed path string "M x y h w v h h -w Z"
- `u_notch(cx, depth, width, opens_toward)` → notch path fragment
- `finger_tab(x, y, tab_w, tab_l, side)` → tab path fragment
- `arc_path(cx, cy, r)` → closed circle path
- `path_union(paths)` → merged closed path (for single-polygon requirement)
- `bounding_box(path_string)` → (x_min, y_min, x_max, y_max)
- `paths_overlap(bbox1, bbox2)` → bool

### `src/loom.py`

Generates `output/loom.svg`. Functions:
- `top_rail()` → single closed path with finger sockets + warp notches + heddle holes
- `bottom_rail()` → single closed path with finger sockets + warp notches
- `stile_L()` → single closed path with finger tabs (top, bottom) + crossbar mortises (inner face)
- `stile_R()` → mirror of stile_L
- `crossbar()` → single closed path (body + tenons, all one rectangle)
- `shuttle()` → single closed path with tapered ends + V-notches + lightening ellipse (separate)
- `beater()` → single closed path (handle + teeth) + grip holes (separate)
- `heddle_bar()` → single closed path + heddle holes (separate)
- `layout()` → places all parts on sheet, verifies no overlaps, writes SVG

### `src/stand.py`

Generates `output/optional_loom_stand.svg` (D-23: 2-piece triangular X easel):
- Two right-triangle pieces, cross-halving half-lap joint at L/2
- Piece A: slot from top edge; Piece B: slot from hypotenuse edge; slots interlock
- Foot tab (TAB_L=30mm, TAB_H=20mm) and bump (5×5mm) on each piece capture loom bottom rail

### `src/box.py`

Generates `output/box.svg` (box parts + stand pieces):
- `box_base()` → single closed path with finger sockets
- `box_long_wall(with_dado=True)` → single closed path with finger tabs + dado groove
- `box_short_wall(open_end=False)` → single closed path
- `lid()` → single closed path (base + grip tab)
- `layout()` → nests all box parts + stand pieces; verifies fit; writes SVG

### `src/test_cut.py`

Generates `output/test_cut.svg`:
- Tab A (nominal 6mm tab)
- Sockets B1 (SOCK_W − 0.1mm), B2 (SOCK_W), B3 (SOCK_W + 0.1mm)
- Dado stub D (2mm groove)
- Lid stubs L1, L2 (MAT3 − 0.1mm, MAT3 + 0.1mm)

### `proofs/invariants.py`

Pure predicate functions — no I/O, no SVG parsing. Each takes a `params` dict and returns `(bool, str)` where str is the proof trace.

```python
def inv_notch_count_pitch(p) -> (bool, str):
    ok = (p['notch_count'] - 1) * p['notch_pitch'] == p['interior_w']
    return ok, f"({p['notch_count']}-1)×{p['notch_pitch']}={...} {'==' if ok else '!='} {p['interior_w']}"

def inv_tab_width(p) -> (bool, str): ...
def inv_no_mortise_3d_overlap(p) -> (bool, str): ...
def inv_parts_on_sheet(p, layout) -> (bool, str): ...
...
```

### `proofs/verify_loom.py`

Parses `output/loom.svg`, extracts bounding boxes of all paths, checks:
- Each path is closed
- No outer path overlaps another outer path
- All bounding boxes within sheet bounds
- Dimensional spot-checks against params (stile height, rail width, notch positions)

---

## Development Stages

| Stage | Gate | Output | Status |
|---|---|---|---|
| 0 — Sparring | Design questions resolved | DECISIONS.md locked | DONE |
| 1 — Proofs | invariants.py written; all invariants stated formally | proofs/invariants.py | DONE |
| 2 — Tests (failing) | All test_*.py written; all fail (no generator yet) | tests/*.py | DONE |
| 3 — params.py | Constants defined; assert invariants pass at import | src/params.py | DONE |
| 4 — geometry.py | Primitive path builders; unit-tested | src/geometry.py | DONE |
| 5 — loom.py | Loom generator; loom tests pass | output/loom.svg | DONE |
| 6 — verify_loom.py | SVG verification passes; inspect actual values | proofs/verify_loom.py | DONE |
| 7 — box.py + stand.py | Box/stand generator; box+stand tests pass | output/optional_box.svg, output/optional_loom_stand.svg | DONE |
| 8 — verify_box.py | Box + assembly verification passes | proofs/verify_box.py | DONE |
| 9 — test_cut.py | Fit test generator | output/test_cut.svg | DONE |
| 10 — parametric | Random size tests; happy + unhappy; generate CLI | tests/test_parametric.py, src/generate.py | DONE |

---

## Working Practices

1. **No src/ edit without a failing test.** Write the test first (it will fail). Then implement. Then verify the test passes and inspect actual output values (not just exit code).

2. **params.py asserts at import.** If invariants fail, the generator does not run. No silent bad geometry.

3. **SVG is never hand-edited.** All geometry is generated by code. The output/ directory is a build artifact.

4. **verify_*.py parses the actual SVG** and checks values — not just that the file was written.

5. **FAILURE_PATTERNS.md is updated after every commit.** The 12-invariant scan (I-1 through I-12 in DECISIONS.md D-12) is run and logged.

6. **DEFECTS.md is updated when any invariant fails** — describe the defect, its root cause, and what check would have caught it earlier.

7. **Parametric test suite** generates at least 5 valid sizes and 5 invalid sizes (e.g., interior too large for sheet, notch pitch inconsistent, tab too narrow). Valid sizes must produce passing SVGs; invalid sizes must raise errors before writing any file.

---

## SVG Conventions

| Element | Stroke | Width | Fill |
|---|---|---|---|
| Cut path (outer boundary) | `#ff0000` | `0.1mm` (preview) / `0.01mm` (laser) | none |
| Cut path (inner hole) | `#ff0000` | same | none |
| Etch label | `#000000` | `0.4mm` | black |
| Sheet boundary (reference only) | `#aaaaaa` | `0.3mm` | light fill |

Generator flag `--laser` switches cut stroke width from 0.1mm to 0.01mm.

All coordinates in mm. SVG viewBox in mm units (1 SVG unit = 1mm).

---

## Stand Geometry (D-23: 2-piece triangular X easel, 6mm ply)

Two identical right-triangle pieces (STAND_X_L × STAND_X_W = 444×80mm for default 400mm interior). Each piece is a 12-point closed polygon:

- **Triangle body:** right angle at (0,0); top edge (0,0)→(L,0); hypotenuse (L,0)→(0,W); foot edge (0,W)→(0,0)
- **Cross-halving slot:** Piece A slot from top edge at x=L/2; Piece B slot from hypotenuse at x=L/2. Both slots depth=W/4=20mm, width=MAT+0.1=6.1mm. Interlock to form X.
- **Foot tab:** Protrudes +y (outward when standing) from hypotenuse at the foot end. TAB_L=30mm, TAB_H=20mm. Loom bottom rail rests on tab ledge.
- **Bump:** 5×5mm step at tab outer end prevents rail sliding off.

Assembly: slot Piece B (slot-from-hyp) down onto Piece A (slot-from-top). Stand on foot edges. Both foot tabs at 20mm height support loom bottom rail.
