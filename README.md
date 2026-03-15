# Laser-Cut Frame Loom

**Status: Draft — ready for test cut validation.**
Next step: cut `output/test_cut.svg` on 3mm scrap and follow `TEST_CUT_CALIBRATION_INSTRUCTIONS.md` before cutting any final material.

A parametric weaving frame loom designed as a gift. All geometry is generated from code — no hand-edited SVGs.

**Weaving interior:** 300×400mm (suitable for a scarf)

## What you get

Four SVG files to cut (loom required; box and stand optional):

| File | Sheet | Parts |
|---|---|---|
| `output/loom.svg` | 6mm birch ply, 600×600mm | 2 rails, 2 stiles, 2 crossbars, heddle bar, 2 shuttles, beater |
| `output/optional_box.svg` | 3mm birch ply, 600×600mm | Storage box (holds disassembled loom flat) with sliding lid |
| `output/optional_loom_stand.svg` | 6mm birch ply, 600×600mm | 2-piece triangular X easel stand (D-23) |
| `output/test_cut.svg` | 3mm scrap | Fit-test calibration pieces — cut this first |


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
```

Default 300×400mm loom (all three SVGs at once):
```bash
.venv/bin/python3 -m src.generate
```

Parametric (custom size, D-29):
```bash
.venv/bin/python3 -m src.generate --width 250 --height 350 --pitch 5
```

Or generate each SVG individually:
```bash
.venv/bin/python3 -m src.loom        # → output/loom.svg
.venv/bin/python3 -m src.box         # → output/optional_box.svg
.venv/bin/python3 -m src.stand       # → output/optional_loom_stand.svg
```

```bash
.venv/bin/python3 -m pytest tests/ -q   # all geometry validated before SVG is written
```

## Key design facts

- N=1 finger joint per corner (tab 7.33mm > material 6mm)
- 61 warp notches at 5mm pitch: (61−1)×5 = 300mm interior width (D-24)
- Two crossbars at 1/3 and 2/3 interior height, mortise pockets in stiles
- Stand: 2-piece triangular X easel, cross-halving half-lap at centre (D-23)
- All parameters in `src/params.py`; 12 geometric invariants checked at generation time

## Docs (for developers)

`docs/DECISIONS.md` — locked design decisions (authoritative)
`docs/FAILURE_PATTERN_REGISTRY.md` — session scan log
`docs/ARCHITECTURE.md` — module structure
