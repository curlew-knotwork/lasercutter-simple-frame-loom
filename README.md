# Laser-cut Frame Loom

A parametric frame loom for weaving, designed as a gift. All geometry is generated from code — no hand-edited SVGs.

**Status:** Code-generated, not yet laser cut. Three SVG outputs in `output/`.

## What it makes

- **300×400mm weaving interior** (suitable for a scarf)
- 6mm birch plywood, 600×600mm sheet
- A-frame stand (3mm ply, same sheet as box)
- Sliding-lid storage box that holds the disassembled loom flat

## Outputs

| File | Sheet | Contents |
|---|---|---|
| `output/loom.svg` | 6mm ply 600×600mm | Rails (×2), stiles (×2), crossbars (×2), shuttle (×2), beater, heddle bar |
| `output/box.svg` | 3mm ply 600×600mm | Box base, lid, 4 walls, stand-L, stand-R, stand spreader |
| `output/test_cut.svg` | 3mm ply scrap | Fit-test pieces — cut this first to verify kerf assumption |

## Generate SVGs

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python3 -m src.loom     # → output/loom.svg
.venv/bin/python3 -m src.box      # → output/box.svg
```

## Run tests

```bash
.venv/bin/python3 -m pytest tests/ -q
```

All geometry is validated by formal invariants at generation time. If any invariant fails the SVG is not written.

## Docs

All design documents are in `docs/`:

| Doc | Purpose |
|---|---|
| `DECISIONS.md` | Locked design decisions — authoritative |
| `REQUIREMENTS.md` | User + system requirements |
| `DESIGN.md` | Design questions and proposals |
| `ARCHITECTURE.md` | Module structure and responsibilities |
| `FAILURE_PATTERN_REGISTRY.md` | 28 failure patterns across 5 categories; session scan log |
| `FAILURE_REGISTRY.md` | Specific defect instances with root cause |

Legacy files (old hand-drawn design, pre-code spec) are in `docs/archive/`.

## Key design decisions

- **N=1 finger joint** per corner: tab 7.33mm > material 6mm ✓ (N=2 gives 4.4mm — too thin)
- **31 warp notches** at 10mm pitch: (31−1)×10 = 300mm = interior width ✓
- **Two crossbars** at 1/3 and 2/3 interior height, inner-face mortises, no prop mortises
- **A-frame stand** from 3mm ply: independent of loom stiles, no mortise conflict
- All parameters live in `src/params.py`; `assert_all()` enforces 12 geometric invariants at import
