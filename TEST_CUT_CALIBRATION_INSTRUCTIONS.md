# Test Cut Calibration

Cut `output/test_cut.svg` before cutting the full loom. It takes a small piece of scrap material and tells you whether the joints will fit.

## Why

Laser kerf (the width of material burned away) varies by machine, material thickness, and focus. This design uses a 0.15mm/side kerf assumption. If your laser burns more or less, joints may be too tight or too loose.

The test file contains sample joints at slightly different clearances so you can pick the one that fits best, then adjust if needed.

## Materials

- Two pieces of scrap from the same batch as your final material
- 3mm birch ply for box joints
- 6mm birch ply for loom/stand joints

Cut the matching test file for each material thickness.

## Procedure

1. **Cut the test file** on your scrap material using the same laser settings (speed, power, focus) you will use for the real parts.

2. **Let it cool** for 1–2 minutes. Wood expands slightly when hot.

3. **Test each sample joint.** The test pieces are numbered. Try fitting them together by hand — no hammer.

   | Feel | What it means |
   |---|---|
   | Drops in freely, wobbles | Too loose — kerf is larger than expected |
   | Slides in with firm hand pressure, stays | Correct fit |
   | Won't go without a mallet | Too tight — kerf is smaller than expected |

4. **Note the number** of the sample that gave the correct fit.

5. **If no sample fits correctly:** adjust laser power or speed by a small amount (5–10%) and repeat. A faster speed or lower power = less kerf = tighter fit. Slower speed or higher power = more kerf = looser fit.

6. **If the best-fit sample is at an extreme** (tightest or loosest available): open `src/params.py`, find the `KERF` parameter, adjust it by 0.05mm in the appropriate direction, regenerate the SVGs, and repeat.

## Acceptance criterion

The correct fit: tab slides in with firm hand pressure (two thumbs), holds without slipping, and can be pulled apart without tools. If it needs a mallet to assemble or a knife to disassemble, it is too tight.

## Note on "6mm" ply

Nominal 6mm birch ply is often actually 5.7–6.2mm. Measure your sheet with calipers at three points and update `MAT` in `src/params.py` if it differs from 6.0mm by more than 0.2mm.
