# Frame Loom — Design Specification
**Version:** 6  
**Date:** 2026-03-06  
**File:** `frame_loom_v6.svg`

---

## 1. Overview

A beginner weaving frame loom designed as a gift. Cut from a single 600×600 mm sheet of 6 mm birch plywood using a laser cutter (Oodi Epilog). The loom includes a fixed-angle kickstand so it can stand at 65° from horizontal on a table, freeing both hands for weaving. A string heddle rod (8 mm dowel, not laser-cut) provides shed control.

Assembly is press-fit with no hardware required. A second 3 mm plywood sheet provides a sliding-lid storage box for the disassembled loom.

---

## 2. Material

| Property | Value |
|---|---|
| Loom sheet | 6 mm birch plywood, 600×600 mm |
| Box sheet | 3 mm birch plywood, 600×600 mm |
| Fit test sheet | 3 mm birch plywood, scrap (~90×32 mm) |
| Heddle rod | 8 mm diameter hardwood dowel, cut to 240 mm |
| Kerf (assumed) | 0.15 mm (verify with fit test before full cut) |

---

## 3. SVG File Convention — CorelDraw / Epilog Workflow

| Colour | Stroke width | Epilog action |
|---|---|---|
| Red `#ff0000` | 0.01 mm (hairline) | Vector **cut** |
| Black `#000000` | 0.4 mm | Vector/raster **etch** |

The preview file `frame_loom_v6_preview.svg` uses 0.1 mm red strokes for visibility in Inkscape. **Use the 0.01 mm version for the laser.**

Every part in the SVG is a **single unified closed outline path**. There are no collections of overlapping rectangles. Inner holes (dowel holes, lightening ellipses) are separate closed paths inside the outer boundary — the laser cuts the outer outline first, then the inner holes.

---

## 4. Frame Dimensions

| Dimension | Value |
|---|---|
| Interior weaving area | 200 × 250 mm |
| Rail width (top and bottom) | 22 mm |
| Stile width (left and right) | 22 mm |
| Frame outer width | 244 mm |
| Frame outer height | 294 mm |
| Material thickness | 6 mm |

The rail width and stile width are equal (22 mm) so that finger joint spacing is identical on both mating parts.

---

## 5. Parts List

| Part | Qty | SVG dimensions | Notes |
|---|---|---|---|
| Top rail | 1 | 244 × 22 mm | Warp notches on bottom edge; dowel holes |
| Bottom rail | 1 | 244 × 22 mm | Warp notches on top edge |
| Left stile | 1 | 22 × 294 mm body | + 6 mm tab protrusions each end; mortises on both faces |
| Right stile | 1 | 22 × 294 mm body | Mirror of left stile for prop mortise |
| Stretcher bar | 1 | 200 mm body + 15 mm tenons = 230 mm total | 6 mm tall |
| Shuttle | 1 | 180 × 28 mm | Tapered ends; V-notches; lightening slot |
| Beater / comb | 1 | 210 × 42 mm | 20 mm teeth; 3 grip holes |
| Prop-L | 1 | 22 × 150 mm | Left-handed bevel; 11 mm tenon |
| Prop-R | 1 | 22 × 150 mm | Right-handed bevel (mirror of Prop-L) |
| **Heddle rod** | 1 | ⌀8 mm × ~240 mm | **Hardwood dowel — not laser cut** |

---

## 6. Finger Joints

Finger joints connect the stile ends to the rail ends. The stiles carry **tabs** (protruding); the rails carry **sockets** (recessed).

### 3D geometry

In the assembled frame, each stile end (22 mm wide × 6 mm thick edge face) inserts into the corresponding rail end socket. The fingers run across the 22 mm width; each finger is 6 mm long (= material thickness).

```
Rail end (plan view):
  ┌──────┬──────┬──────┐
  │ gap  │ sock │ gap  │   ← socket opens to receive stile tab
  │      │      │      │
  └──────┴──────┴──────┘
     7.33   7.33   7.33 mm (3 segments of 22/3)

Stile top end (plan view):
  ┌──────┬──────┬──────┐
  │ gap  │ TAB  │ gap  │   ← 1 central tab, 7.33 mm wide, 6 mm tall
  └──────┴──────┴──────┘
```

### Dimensions

| Parameter | Value | Rationale |
|---|---|---|
| Fingers per joint | 1 central tab | N=2 gives 4.4 mm width < MAT=6 mm — too narrow; N=1 gives 7.33 mm > 6 mm ✓ |
| Finger width (tab/socket) | 7.33 mm | `STILE_W / (2×1+1)` = `22/3` |
| Finger length | 6.0 mm | = `MAT` — stile inserts fully into rail |
| Tab drawn width in SVG | 6.0 mm | Laser reduces by ~2×kerf → ~5.7 mm actual |
| Socket drawn width in SVG | 6.1 mm | Laser increases by ~2×kerf → ~6.4 mm actual |
| Net clearance after cutting | ~0.1 mm | Snug press-fit, no glue required for test; glue for final |

---

## 7. Warp Notches

Notches are cut into the inner edge of both rails to hold warp threads under tension.

| Parameter | Value |
|---|---|
| Number of notches | 20 |
| Pitch | 10 mm |
| Notch width | 4.0 mm |
| Notch depth | 5.0 mm |
| Start position (from rail outer edge) | 22 mm (= stile width — notches begin at inner stile face) |
| End position | 222 mm (= frame outer width − stile width) |
| Yarn size | Suitable for 1–4 mm diameter yarn |

Top rail notches open **downward** (toward weaving interior).  
Bottom rail notches open **upward** (toward weaving interior).

---

## 8. Heddle Rod Dowel Holes

Two holes in the **top rail** accept an 8 mm diameter dowel as the heddle rod. String heddles are tied to the rod and loop around alternate warp threads to create a shed.

| Parameter | Value |
|---|---|
| Hole diameter | 8.0 mm (⌀8) |
| Hole drawn radius in SVG | 4.0 mm |
| Left hole centre | x = 36 mm from left outer rail edge, y = 11 mm (rail centreline) |
| Right hole centre | x = 208 mm from left outer rail edge (symmetric) |
| Clear of finger socket zone | ✓ — socket zone is x = 0–6 mm; holes at x = 32–40 mm |

---

## 9. Stile Mortises

Each stile has two mortise slots on **opposite faces** — no material conflict.

### Stretcher mortise (inner face)

Accepts the stretcher bar tenon. Opens from the **inner face** of each stile (the face toward the weaving interior) at mid-height.

| Parameter | Value |
|---|---|
| Position along stile height | `FRAME_H/2 − 3.05` = ~143.9 mm from stile top |
| Width (along stile height) | 6.1 mm (= `SOCK_W`) |
| Depth (into stile face) | 15 mm (= `STRETCH_TEN`) |
| Remaining stile material | 22 − 15 = 7 mm ✓ |

### Prop mortise (outer face)

Accepts the prop arm tenon. Opens from the **outer face** (back face, away from weaving interior) at `PIVOT_H = 150 mm` from stile bottom.

| Parameter | Value |
|---|---|
| Position from stile bottom | 150 mm |
| Width (along stile height) | 6.1 mm (= `SOCK_W`) |
| Depth (into stile face) | 11 mm (`PROP_MORT_D`) — half stile width, preserving strength |
| Remaining stile material | 22 − 11 = 11 mm ✓ |

**Left stile vs right stile:** The stretcher mortise is on the right face of the left stile and the left face of the right stile (both inner faces). The prop mortise is on the left face of the left stile and the right face of the right stile (both outer faces). The parts are **not interchangeable**.

---

## 10. Stretcher Bar

A single horizontal cross-brace that prevents the frame from bowing under warp tension.

| Parameter | Value |
|---|---|
| Body width | 200 mm (= `WEAVE_W` — spans between stile inner faces) |
| Body height | 6 mm (= `MAT`) |
| Tenon length each end | 15 mm |
| Total length | 230 mm |
| Tenon width | 6.0 mm (`TAB_W`) |
| Tenon vertical position | Centred on 6 mm body height |
| Mortise position on stile | Mid-height of frame (147 mm from top of stile body) |

---

## 11. Prop Arms

Two prop arms (Prop-L and Prop-R) slot into the outer face mortises of each stile and hold the frame at 65° from horizontal.

### Geometry

The prop is a flat piece that leans at **25° from vertical** when deployed. The foot is bevelled so it sits flat on the table at this angle.

| Parameter | Value |
|---|---|
| Frame working angle | 65° from horizontal |
| Prop lean angle | 25° from vertical |
| Pivot height on stile | 150 mm from stile bottom |
| Pivot height above table (at 65°) | 135.9 mm |
| Prop length | 150 mm |
| Prop body width | 22 mm |
| Tenon length | 11 mm (= `PROP_MORT_D`) |
| Tenon width | 6.1 mm (`SOCK_W`) |
| Foot bevel depth | 10.3 mm across 22 mm width = 25° ✓ |
| Table footprint behind frame | ~124 mm |

### Left vs Right

Prop-L and Prop-R are **mirror images**. The bevel cut on Prop-L shortens the right corner of the foot; the bevel on Prop-R shortens the left corner. Using the wrong prop on the wrong stile will leave the foot rocking on a corner instead of sitting flat.

- **Prop-L** → Left stile (outer face = left edge of frame)
- **Prop-R** → Right stile (outer face = right edge of frame)

### Operation

Slot the tenon straight into the stile mortise from outside. The prop is a fixed-angle fit — it holds at 65° with no hinge mechanism. To store, pull the props out and lay them flat behind the frame.

---

## 12. Shuttle

| Parameter | Value |
|---|---|
| Length | 180 mm |
| Width | 28 mm |
| Taper length | 22 mm each end |
| Yarn V-notch half-width | 5 mm |
| Lightening ellipse | 110 × 12 mm centred |

The V-notches are cut **into** the tapered tip outline — they are part of the single unified path, not separate circles.

---

## 13. Beater / Comb

| Parameter | Value |
|---|---|
| Total width | 210 mm |
| Handle height | 22 mm |
| Tooth height | 20 mm |
| Tooth width | 4 mm |
| Tooth gap | 6 mm |
| Grip holes | 3 × ellipse, 16 × 7 mm, evenly spaced |

---

## 14. Sheet Layout

All parts nest onto a single 600×600 mm sheet with no overlaps. Bounding boxes (absolute sheet coordinates):

| Part | x range (mm) | y range (mm) | Size |
|---|---|---|---|
| Top rail | 2 – 258 | 22 – 49 | 256 × 27 mm |
| Bottom rail | 2 – 258 | 55 – 82 | 256 × 27 mm |
| Left stile | 14 – 62 | 88 – 394 | 48 × 306 mm |
| Right stile | 64 – 112 | 88 – 394 | 48 × 306 mm |
| Stretcher | 8 – 238 | 400 – 406 | 230 × 6 mm |
| Shuttle | 278 – 458 | 22 – 50 | 180 × 28 mm |
| Beater | 278 – 488 | 56 – 98 | 210 × 42 mm |
| Prop-L | 278 – 300 | 104 – 254 | 22 × 150 mm |
| Prop-R | 306 – 328 | 104 – 254 | 22 × 150 mm |

The stile bounding boxes (48 mm wide) include the 15 mm stretcher tenon protrusion and 11 mm prop mortise protrusion from opposite faces. The stile body itself is 22 mm wide.

---

## 15. Fit Test (before cutting the loom)

Cut `fit_test_v2.svg` from a **scrap piece of 3 mm ply** (~90×32 mm) before committing either full sheet. This tests the socket width and dado groove fit specific to the Oodi Epilog settings on the day.

| Piece | Tests |
|---|---|
| A | Tab piece — press into B1, B2, B3 |
| B1 | Socket 3.00 mm (tight) |
| B2 | Socket 3.10 mm (nominal) |
| B3 | Socket 3.20 mm (loose) |
| D | Dado wall stub — 2 mm groove × 20 mm wide |
| L1 | Lid stub 2.9 mm wide |
| L2 | Lid stub 3.1 mm wide |

**Pass criteria:** A into B2 should require light hand pressure and hold without any tool. If B1 fits better, reduce `SOCK_W` to 3.00 mm. If B3 is needed, increase to 3.20 mm. Update the box SVG accordingly before cutting.

---

## 16. Storage Box

A sliding-lid box cut from 3 mm birch plywood holds the fully disassembled loom flat.

| Parameter | Value |
|---|---|
| Interior | 260 × 310 × 21 mm |
| Outer | 266 × 316 × 24 mm |
| Material | 3 mm birch plywood |
| Finger joint pitch | ~3.0 mm throughout |
| Tab drawn width | 3.0 mm |
| Socket drawn width | 3.1 mm |
| Dado groove depth | 2.0 mm |
| Dado groove width | 3.2 mm |
| Lid | 263.7 × 326 mm (includes 10 mm grip tab) |
| Lid clearance in dado | 0.1 mm each side |

### Box parts

| Part | Qty | Size |
|---|---|---|
| Base | 1 | 266 × 316 mm |
| Long wall | 2 | 316 × 21 mm (with dado groove on top edge) |
| Short wall closed | 1 | 260 × 21 mm |
| Short wall open | 1 | 260 × 21 mm (with lid exit slot) |
| Lid | 1 | 263.7 × 326 mm |

### Box assembly order

1. Press long wall tabs into base sockets (×2)
2. Press closed short wall into position
3. Slide lid into long wall dado grooves from the open end
4. Press open short wall in last — lid remains accessible for sliding out

---

## 17. MDF Instruction Sheet

Assembly instructions and part labels should be laser-etched onto a separate MDF piece (not included in the cut SVGs). Suggested content:

- Part labels: TOP RAIL, BOTTOM RAIL, LEFT STILE, RIGHT STILE, STRETCHER, SHUTTLE, BEATER, PROP-L, PROP-R
- Assembly sequence (steps 1–7)
- Prop lean diagram showing 65° working angle
- Warp threading diagram
- Heddle rod setup: 8 mm dowel through top rail holes; string heddles tied around alternate warp threads

---

## 18. Assembly Sequence

1. Press **left stile** tabs into **top rail** left sockets and **bottom rail** left sockets
2. Press **right stile** tabs into **top rail** right sockets and **bottom rail** right sockets
3. Slide **stretcher** tenons into the inner-face mortises of both stiles (mid-height)
4. Insert **heddle rod** (8 mm dowel) through the two holes in the top rail
5. Thread **warp**: loop yarn from top-rail notch down to matching bottom-rail notch, repeat across all 20 pairs
6. Slot **Prop-L** tenon into the left stile outer-face mortise; **Prop-R** into the right — frame stands at 65°
7. Tie **string heddles** around alternate warp threads on the heddle rod
8. Weave with **shuttle**; beat with **comb**

---

## 19. Design Decisions Log

| Decision | Rationale |
|---|---|
| Interior 200×250 mm | Standard beginner gift size — fits a scarf panel or small wall hanging |
| 10 mm warp notch pitch | Beginner-friendly; works with chunky yarn (≥2 mm) |
| N=1 finger per corner joint | N=2 gives 4.4 mm fingers narrower than MAT=6 mm — mechanically weak |
| String heddle rod, not rigid heddle | Simpler, no precision slots required; beginner learns the technique naturally |
| Stretcher bar at mid-height | Prevents frame bow under warp tension — biggest structural flaw in original design |
| Prop mortise depth 11 mm (not 22 mm) | Full-depth mortise would bisect the stile; 11 mm leaves 11 mm of material each side |
| Prop at 150 mm from stile bottom | Lower pivot gives 38 mm footprint (marginal); 150 mm gives 124 mm footprint (stable) |
| Props as separate removable pieces | Flat laser-cut props cannot pivot in 3D — fixed-angle slot-in is the only viable mechanism without hardware |
| Text stripped from cut SVG | All labels etched on separate MDF — reduces cut time and cost on plywood |

---

## 20. Known Limitations

- The 7 mm of stile material remaining after the stretcher mortise is thin. Do not overtighten warp tension. Gluing the frame joints is recommended for long-term use.
- The prop stand is designed for use on a flat, non-slip surface. A rubberised mat under the prop feet prevents the frame sliding forward during vigorous beating.
- Warp notch width 4 mm accepts yarn up to ~4 mm diameter. Fine thread (< 1 mm) may slip out of the notch; a thin strip of tape across the notch base can prevent this.
- The fit test must be run before cutting the full box sheet — kerf at Oodi may differ from the 0.15 mm assumption used in the SVG dimensions.
