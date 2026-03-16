"""
tests/test_parametric.py — Parametric size coverage.

Stage 10 (ARCHITECTURE.md): verify that:
  - 5+ valid (interior_w, interior_h, notch_pitch) triples produce all-passing invariants AND
    a loom layout with no verification failures.
  - 5+ invalid parameter sets raise ValueError or AssertionError before any SVG is written.

interior_w must be divisible by notch_pitch for I-8 to hold (D-24, D-29).
Reference: DECISIONS.md D-12 (I-1 through I-12), D-29, ARCHITECTURE.md § Stage 10.
"""

import re
import pytest

from src.params import make_params
from proofs.invariants import assert_all, check_all
import src.loom as loom_mod
import src.box as box_mod


# ---------------------------------------------------------------------------
# Valid sizes — 5 distinct (interior_w, interior_h, notch_pitch) triples
# Each must satisfy every invariant and produce a clean loom layout.
# interior_w must be divisible by notch_pitch (I-8 requirement, D-24, D-29).
# All interior_w in [150,500] and interior_h in [200,550] (D-29 ranges).
# ---------------------------------------------------------------------------

VALID_SIZES = [
    # (interior_w, interior_h, notch_pitch, min_tooth_w, description)
    # pitch=5mm entries use min_tooth_w=2.0 (explicit opt-out of 4mm ply floor; D-37).
    # Default design (pitch=10mm) uses min_tooth_w=4.0 and must itself pass I-13.
    (150.0, 200.0, 5.0,  2.0, "small (150×200mm, 5mm pitch)"),
    (200.0, 300.0, 5.0,  2.0, "compact portrait (200×300mm)"),
    (300.0, 400.0, 5.0,  2.0, "default scarf (300×400mm)"),
    (250.0, 350.0, 5.0,  2.0, "medium portrait (250×350mm)"),
    (300.0, 400.0, 10.0, 4.0, "default scarf, chunky pitch"),
]


@pytest.mark.parametrize("iw,ih,pitch,mtw,desc", VALID_SIZES)
def test_valid_params_all_invariants_pass(iw, ih, pitch, mtw, desc):
    """All invariants (I-3 through I-13) must pass for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch, min_tooth_w=mtw)
    results = check_all(p)
    failures = [(name, trace) for name, ok, trace in results if not ok]
    assert failures == [], f"Invariant failures for {desc}:\n" + "\n".join(
        f"  {n}: {t}" for n, t in failures
    )


@pytest.mark.parametrize("iw,ih,pitch,mtw,desc", VALID_SIZES)
def test_valid_params_notch_invariant(iw, ih, pitch, mtw, desc):
    """I-8: (notch_count-1)*pitch == interior_w for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch, min_tooth_w=mtw)
    span = (p["NOTCH_COUNT"] - 1) * p["NOTCH_PITCH"]
    assert abs(span - p["INTERIOR_W"]) < 1e-9, (
        f"{desc}: span={span} != INTERIOR_W={p['INTERIOR_W']}"
    )


@pytest.mark.parametrize("iw,ih,pitch,mtw,desc", VALID_SIZES)
def test_valid_params_tab_wider_than_mat(iw, ih, pitch, mtw, desc):
    """I-5: TAB_W > MAT for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch, min_tooth_w=mtw)
    assert p["TAB_W"] > p["MAT"], (
        f"{desc}: TAB_W={p['TAB_W']:.4f} <= MAT={p['MAT']:.4f}"
    )


@pytest.mark.parametrize("iw,ih,pitch,mtw,desc", VALID_SIZES)
def test_valid_params_loom_layout_verifies_clean(iw, ih, pitch, mtw, desc):
    """Loom layout verify() must return no failures for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch, min_tooth_w=mtw)
    placed = loom_mod.layout(p)
    results = loom_mod.verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    assert failures == [], f"loom.verify() failures for {desc}:\n" + "\n".join(
        f"  {n}: {d}" for n, d in failures
    )


@pytest.mark.parametrize("iw,ih,pitch,mtw,desc", VALID_SIZES)
def test_valid_params_loom_svg_all_paths_closed(iw, ih, pitch, mtw, desc):
    """I-12: every cut path in the generated loom SVG must end with Z."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch, min_tooth_w=mtw)
    svg = loom_mod.generate(p)
    paths = re.findall(r' d="([^"]+)"', svg)
    assert paths, f"{desc}: no path data found in SVG"
    open_paths = [d[:60] for d in paths if not d.rstrip().endswith("Z")]
    assert open_paths == [], (
        f"{desc}: {len(open_paths)} open path(s) found:\n  "
        + "\n  ".join(open_paths)
    )


@pytest.mark.parametrize("iw,ih,pitch,mtw,desc", VALID_SIZES)
def test_valid_params_box_layout_verifies_clean(iw, ih, pitch, mtw, desc):
    """Box layout verify() must return no failures for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch, min_tooth_w=mtw)
    placed = box_mod.layout(p)
    results = box_mod.verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    assert failures == [], f"box.verify() failures for {desc}:\n" + "\n".join(
        f"  {n}: {d}" for n, d in failures
    )


# ---------------------------------------------------------------------------
# Invalid sizes — parameter sets that must raise ValueError or AssertionError.
# D-29 range violations raise ValueError (before assert_all).
# Invariant violations raise AssertionError.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kwargs,match,desc", [
    ({"interior_w": 293.0},  "divisible", "interior_w=293 not divisible by notch_pitch=5"),
    ({"interior_h": 5000.0}, "interior_h", "interior_h=5000 out of range"),
    ({"interior_w": 600.0},  "interior_w", "interior_w=600 out of range"),
    ({"interior_h": 30.0},   "interior_h", "interior_h=30 too small"),
    ({"notch_pitch": 3.0},   "notch_pitch", "pitch=3 too small"),
])
def test_invalid_params_raise_value_error(kwargs, match, desc):
    """make_params() must raise ValueError for D-29 range violations."""
    with pytest.raises(ValueError, match=match):
        make_params(**kwargs)


@pytest.mark.parametrize("kwargs,inv,desc", [
    ({"mat": 8.0}, "I-5", "mat=8.0 → TAB_W=7.33 < MAT=8.0 (tab too narrow)"),
])
def test_invalid_params_raise_assertion_error(kwargs, inv, desc):
    """make_params() must raise AssertionError for invariant violations."""
    with pytest.raises(AssertionError, match="INVARIANT FAILURES"):
        make_params(**kwargs)
