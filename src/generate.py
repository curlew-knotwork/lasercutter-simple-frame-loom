"""
src/generate.py — CLI entry point: generate all SVGs for a parametric loom.

Usage:
    python -m src.generate                           # default 300×400mm, 5mm pitch
    python -m src.generate --width 300 --height 400  # explicit
    python -m src.generate --width 200 --height 300 --pitch 5
    python -m src.generate --width 300 --height 400 --pitch 10  # chunky
    python -m src.generate --mat 6.0 --kerf 0.15

Writes:
    output/loom.svg                6mm ply, loom frame + accessories
    output/optional_box.svg        3mm ply, storage box
    output/optional_loom_stand.svg 6mm ply, 2-piece X easel stand

All three are verified before writing. Exits 1 if any verification fails.
"""

import argparse
import sys

from src.params import make_params
import src.loom as loom_mod
import src.box as box_mod
import src.stand as stand_mod


def run(interior_w, interior_h, notch_pitch, mat, kerf):
    try:
        p = make_params(
            interior_w=interior_w,
            interior_h=interior_h,
            notch_pitch=notch_pitch,
            mat=mat,
            kerf=kerf,
        )
    except (ValueError, AssertionError) as e:
        print(f"ERROR: invalid parameters — {e}", file=sys.stderr)
        return 1

    ok = True
    for mod, name in [
        (loom_mod,  "loom"),
        (box_mod,   "box"),
        (stand_mod, "stand"),
    ]:
        try:
            path = mod.write(p)
            print(f"  {name}: OK — {path}")
        except (ValueError, AssertionError) as e:
            print(f"ERROR: {name} failed — {e}", file=sys.stderr)
            ok = False

    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Generate laser-cut frame loom SVGs.")
    ap.add_argument("--width",  type=float, default=300.0, metavar="W",
                    help="Interior weaving width mm [150-500] (default 300)")
    ap.add_argument("--height", type=float, default=400.0, metavar="H",
                    help="Interior weaving height mm [200-550] (default 400)")
    ap.add_argument("--pitch",  type=float, default=5.0,   metavar="P",
                    help="Warp notch pitch mm [4-15] (default 5)")
    ap.add_argument("--mat",    type=float, default=6.0,   metavar="M",
                    help="Loom material thickness mm (default 6)")
    ap.add_argument("--kerf",   type=float, default=0.15,  metavar="K",
                    help="Kerf per cut side mm (default 0.15)")
    args = ap.parse_args()
    sys.exit(run(args.width, args.height, args.pitch, args.mat, args.kerf))


if __name__ == "__main__":
    main()
