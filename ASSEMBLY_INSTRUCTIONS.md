# Assembly Instructions

All joints are laser-cut press-fits. No glue or tools required. A rubber mallet can help with stubborn joints; protect the wood with a scrap block.

---

## Generating Cut Files

The default SVGs use a **0.3mm preview stroke** visible in design software. Before sending to the laser cutter, regenerate with the `--laser` flag to switch to the **0.01mm hairline stroke** required by most laser software:

```
python -m src.generate --laser
```

This overwrites `output/loom.svg`, `output/optional_box.svg`, and `output/optional_loom_stand.svg` in place.

---

## Before You Start

**Remove char from edges.** Laser cutting leaves black soot on cut edges. If not removed, it will rub off onto your yarn.

- Lightly sand all edges with 220-grit sandpaper, or wipe with a damp cloth
- Pay extra attention to the warp notches (the teeth on the rails) and any slot that yarn will touch
- Let wood dry completely before assembling

---

## Loom Frame

**Parts (from `loom.svg`, 6mm birch ply):**

| Part | Description |
|---|---|
| Rail (×2) | Horizontal top and bottom bars with warp notches (the "teeth") |
| Stile (×2) | Vertical side pieces |
| Crossbar (×2) | Interior horizontal braces |
| Heddle bar (×1) | Notched bar to keep warp threads spaced |
| Shuttle (×2) | Flat tool for carrying weft yarn |
| Beater (×1) | Comb for packing weft rows |

**Assembly order:**

1. **Crossbars first.** Lay one stile flat. Slide the two crossbars into the rectangular mortise pockets on the inner face of the stile. The crossbars sit flush; no tenons. Firm hand pressure. Repeat for the second stile.

2. **Rail corners.** Stand the two stiles upright (crossbars horizontal between them). Press a rail's finger tabs into the socket at the top of each stile. Work one corner at a time. The tab should seat fully — flush with the stile face.

3. **Bottom rail.** Same as above for the bottom rail.

4. **Check square.** Measure diagonally corner to corner (top-left to bottom-right, then top-right to bottom-left). Measurements should be equal. If not, press one corner in slightly until square.

5. **Heddle bar, shuttles, beater** need no assembly — they are ready to use.

**Fit notes:**
- Joints should be tight but not require a hammer. If a joint is too tight, lightly sand the tab (not the socket).
- If a joint is too loose, a small strip of masking tape on the tab will take up slack.
- Run `test_cut.svg` first (see `TEST_CUT_CALIBRATION_INSTRUCTIONS.md`) to verify fit before cutting the full loom.

---

## Storage Box (optional)

**Parts (from `optional_box.svg`, 3mm birch ply):**

| Part | Description |
|---|---|
| Base panel (×1) | Floor of the box |
| Wall panels (×4) | Front, back, left, right |
| Lid (×1) | Slides into grooves at top of front/back walls |

**Assembly:**

1. **Walls.** Press the four wall panels together at the corners using the finger joints. Work your way around — press one joint halfway, then move to the next, then come back and fully seat each one.

2. **Base.** Press the base panel up into the bottom slots of the assembled walls. It should click in flush.

3. **Lid.** Slide the lid into the groove at the top of the front and back walls. It should slide smoothly. If tight, sand the lid edges lightly along the grain.

4. **Loading.** The box is sized to hold the disassembled loom flat. Pack in this order: crossbars first (flat on base), then rails, then stiles on top.

**Fit notes:**
- Finger joints on 3mm ply are more delicate than the 6mm loom joints. Press evenly — no twisting.
- Wood glue is optional if you want the box to be permanent. Apply sparingly to finger joints only; wipe excess immediately.

---

## Loom Stand (optional)

**Parts (from `optional_loom_stand.svg`, 6mm birch ply):**

| Part | Label on piece | Description |
|---|---|---|
| Stand X-A (×1) | STAND X-A | First triangle arm (slot from top) |
| Stand X-B (×1) | STAND X-B | Second triangle arm (same cut, assembled flipped) |

Both pieces are cut identically. The slot position and foot tab are the same on both cuts.

**How the joint works:** The two pieces interlock via cross-halving half-lap joints at their centres. One piece has its slot facing up; the other is flipped horizontally so its slot faces down. They slide together at the crossing to form an X.

The foot tabs (short horizontal extensions at the wide end of each piece) face inward after assembly and cradle the loom's bottom rail. The small bump at the end of each tab prevents the rail from sliding off.

**Assembly:**

1. Take piece STAND X-B. Flip it horizontally (left-to-right) so its slot faces down and its foot tab points to the right.

2. Hold STAND X-A with the slot facing up. Lower STAND X-B (slot-down) onto STAND X-A (slot-up), aligning the two slots at the crossing point. Press together until both pieces are flush — the slots interlock at the midpoint.

3. Stand the assembled X upright on a flat surface. Both foot tabs point inward, toward each other.

4. **Place loom.** Slide the loom frame down so the bottom rail rests on the two foot tabs. The bumps at the tab ends stop the rail. The loom leans back at a comfortable weaving angle.

**Stability notes:**
- Place the stand on a flat surface. The wide triangular footprint is self-stable.
- The lean angle is set by the triangle geometry — no adjustment needed.
- To disassemble: lift the loom off, then slide the two X pieces apart at the crossing.
