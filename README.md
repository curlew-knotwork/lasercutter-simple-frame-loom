# Laser-Cut Frame Loom

A parametric weaving frame loom designed as a gift. All geometry is generated from code — no hand-edited SVGs.

**Weaving interior:** 300×400mm (suitable for a scarf)

## What you get

Three SVG files to cut, plus a test file:

| File | Sheet | Parts |
|---|---|---|
| `output/loom.svg` | 6mm birch ply, 600×600mm | 2 rails, 2 stiles, 2 crossbars, heddle bar, 2 shuttles, beater |
| `output/optional_box.svg` | 3mm birch ply, 600×600mm | Storage box (holds disassembled loom flat) with sliding lid |
| `output/optional_loom_stand.svg` | 6mm birch ply, 600×600mm | Triangle stand (8 parts) |
| `output/test_cut.svg` | 3mm scrap | Fit-test calibration pieces — cut this first |

The loom is the only required file. The box and stand are optional.

## Quick start

### 1. Cut and calibrate

Cut `test_cut.svg` first on scrap material. See `TEST_CUT_CALIBRATION_INSTRUCTIONS.md` for how to pick the right fit.

### 2. Cut the loom

Send `loom.svg` to your laser cutter. Material: 6mm birch plywood, 600×600mm sheet.

### 3. Assemble

See `ASSEMBLY_INSTRUCTIONS.md`. No tools required — all joints are hand press-fit.

### 4. Weave

See `LOOM_USER_GUIDE.md` for warping, heddle bar use, weaving technique, and tips.

## Generate SVGs yourself

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python3 -m src.loom        # → output/loom.svg
.venv/bin/python3 -m src.box         # → output/optional_box.svg
.venv/bin/python3 -m src.stand       # → output/optional_loom_stand.svg
```

```bash
.venv/bin/python3 -m pytest tests/ -q   # all geometry validated before SVG is written
```

## Key design facts

- N=1 finger joint per corner (tab 7.33mm > material 6mm)
- 31 warp notches at 10mm pitch: (31−1)×10 = 300mm interior width
- Two crossbars at 1/3 and 2/3 interior height, mortise pockets in stiles
- Triangle stand: solid 6mm ply right-triangle sides + 6 cross members, L-shaped drop-in joints
- All parameters in `src/params.py`; 12 geometric invariants checked at generation time

## Docs (for developers)

`docs/DECISIONS.md` — locked design decisions (authoritative)
`docs/FAILURE_PATTERN_REGISTRY.md` — session scan log
`docs/ARCHITECTURE.md` — module structure
