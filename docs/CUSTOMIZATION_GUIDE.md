# Customization Guide

## Overview

Three primary knobs control the loom. Everything else (frame, box, stand, beater, heddle bar, shuttle) is derived automatically.

| Knob | Flag | Default | Range | Notes |
|---|---|---|---|---|
| Interior width | `--width` | 300mm | 150–500mm | Must be divisible by pitch |
| Interior height | `--height` | 400mm | 200–550mm | |
| Warp pitch | `--pitch` | 5mm | 4–15mm | Sets epi; must divide width evenly |

Material overrides (set once from test-cut results):

| Knob | Flag | Default | Notes |
|---|---|---|---|
| Loom material thickness | `--mat` | 6mm | Measure actual sheet before cutting |
| Kerf per side | `--kerf` | 0.15mm | Tune from test-cut fit |

## Examples

### Small (150×200mm, 5mm pitch — card weaving, wall art)
```
python -m src.generate --width 150 --height 200 --pitch 5
```
- 31 warp threads
- Shuttle: 120mm
- Fits on single 600×600mm sheet

### Medium — default scarf (300×400mm, 5mm pitch)
```
python -m src.generate
```
- 61 warp threads
- Shuttle: 180mm
- Outputs: loom.svg, optional_box.svg, optional_loom_stand.svg

### Chunky yarn (300×400mm, 10mm pitch)
```
python -m src.generate --width 300 --height 400 --pitch 10
```
- 31 warp threads
- Shuttle: 180mm
- Use chunky or bulky yarn (≥10mm pitch → 4mm notch)

## What auto-derives

| Parameter | Formula | Example (default 300×400, 5mm) |
|---|---|---|
| Warp notch count | `interior_w / pitch + 1` | 61 |
| Notch width | `pitch × 0.4` | 2mm |
| Beater tooth width | `= notch_w` | 2mm |
| Beater tooth height | `min(notch_w × 6.5, 20)` | 13mm |
| Shuttle length | `clamp(width × 0.6, 120, 280), rounded to 5mm` | 180mm |
| Shuttle lightening ellipse | `shuttle_l − 2×taper − 10mm` | 114mm |
| Stand arm length | `interior_h + 2 × 22mm` | 444mm |
| Box interior | Derived from longest part + clearance | auto |

## Constraints

- `interior_w` must be an exact multiple of `notch_pitch`. If not, you will get a clear error message.
- Material must satisfy `stile_w/3 > mat` (tab strength). At mat=6mm this requires stile_w=22mm, which is fixed.
- The loom, box, and stand all fit on a 600×600mm sheet. Very large sizes (stile_total_h > ~560mm) will cause sheet-overflow errors in layout.

## Running the test cut first

Before cutting the full loom, always run the test cut:
```
python -m src.test_cut
```
Then measure the fit. Adjust `--mat` and `--kerf` to match your actual laser and sheet.
