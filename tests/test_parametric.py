"""
tests/test_parametric.py — Parametric size coverage.

Stage 10 (ARCHITECTURE.md): verify that:
  - 5+ valid (interior_w, interior_h) pairs produce all-passing invariants AND
    a loom layout with no verification failures.
  - 5+ invalid parameter sets raise AssertionError before any SVG is written.

interior_w must be a multiple of NOTCH_PITCH=10 for I-8 to hold.
Reference: DECISIONS.md D-12 (I-1 through I-12), ARCHITECTURE.md § Stage 10.
"""

import re
import pytest

from src.params import make_params
from proofs.invariants import assert_all, check_all
import src.loom as loom_mod
import src.box as box_mod


# ---------------------------------------------------------------------------
# Valid sizes — 5 distinct (interior_w, interior_h) pairs
# Each must satisfy every invariant and produce a clean loom layout.
# All interior_w values are multiples of NOTCH_PITCH=10 (I-8 requirement).
# ---------------------------------------------------------------------------

VALID_SIZES = [
    # (interior_w, interior_h, description)
    (100.0, 150.0, "small square-ish (100×150mm)"),
    (200.0, 300.0, "compact portrait (200×300mm)"),
    (300.0, 400.0, "default scarf (300×400mm)"),
    (250.0, 350.0, "medium portrait (250×350mm)"),
    (150.0, 250.0, "compact portrait (150×250mm)"),
]


@pytest.mark.parametrize("iw,ih,desc", VALID_SIZES)
def test_valid_params_all_invariants_pass(iw, ih, desc):
    """All invariants (I-3 through I-11) must pass for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih)
    results = check_all(p)
    failures = [(name, trace) for name, ok, trace in results if not ok]
    assert failures == [], f"Invariant failures for {desc}:\n" + "\n".join(
        f"  {n}: {t}" for n, t in failures
    )


@pytest.mark.parametrize("iw,ih,desc", VALID_SIZES)
def test_valid_params_notch_invariant(iw, ih, desc):
    """I-8: (notch_count-1)*pitch == interior_w for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih)
    span = (p["NOTCH_COUNT"] - 1) * p["NOTCH_PITCH"]
    assert abs(span - p["INTERIOR_W"]) < 1e-9, (
        f"{desc}: span={span} != INTERIOR_W={p['INTERIOR_W']}"
    )


@pytest.mark.parametrize("iw,ih,desc", VALID_SIZES)
def test_valid_params_tab_wider_than_mat(iw, ih, desc):
    """I-5: TAB_W > MAT for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih)
    assert p["TAB_W"] > p["MAT"], (
        f"{desc}: TAB_W={p['TAB_W']:.4f} <= MAT={p['MAT']:.4f}"
    )


@pytest.mark.parametrize("iw,ih,desc", VALID_SIZES)
def test_valid_params_loom_layout_verifies_clean(iw, ih, desc):
    """Loom layout verify() must return no failures for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih)
    placed = loom_mod.layout(p)
    results = loom_mod.verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    assert failures == [], f"loom.verify() failures for {desc}:\n" + "\n".join(
        f"  {n}: {d}" for n, d in failures
    )


@pytest.mark.parametrize("iw,ih,desc", VALID_SIZES)
def test_valid_params_loom_svg_all_paths_closed(iw, ih, desc):
    """I-12: every cut path in the generated loom SVG must end with Z."""
    p = make_params(interior_w=iw, interior_h=ih)
    svg = loom_mod.generate(p)
    paths = re.findall(r' d="([^"]+)"', svg)
    assert paths, f"{desc}: no path data found in SVG"
    open_paths = [d[:60] for d in paths if not d.rstrip().endswith("Z")]
    assert open_paths == [], (
        f"{desc}: {len(open_paths)} open path(s) found:\n  "
        + "\n  ".join(open_paths)
    )


@pytest.mark.parametrize("iw,ih,desc", VALID_SIZES)
def test_valid_params_box_layout_verifies_clean(iw, ih, desc):
    """Box layout verify() must return no failures for each valid size."""
    p = make_params(interior_w=iw, interior_h=ih)
    placed = box_mod.layout(p)
    results = box_mod.verify(placed, p)
    failures = [(n, d) for n, ok, d in results if not ok]
    assert failures == [], f"box.verify() failures for {desc}:\n" + "\n".join(
        f"  {n}: {d}" for n, d in failures
    )


# ---------------------------------------------------------------------------
# Invalid sizes — 5 parameter sets that must raise AssertionError.
# make_params() calls assert_all() internally; no SVG is written.
# ---------------------------------------------------------------------------

INVALID_SIZES = [
    # (kwargs, violated_invariant, description)
    (
        {"interior_w": 295.0},
        "I-8",
        "interior_w=295 not a multiple of NOTCH_PITCH=10 → span=300≠295",
    ),
    (
        {"interior_h": 5000.0},
        "I-1",
        "interior_h=5000 → stile_total_h=5056mm >> SHEET_H=600mm",
    ),
    (
        {"interior_w": 600.0},
        "I-1",
        "interior_w=600 → frame_outer_w=644mm > SHEET_W=600mm",
    ),
    (
        {"mat": 8.0},
        "I-5",
        "mat=8.0 → TAB_W=7.33 < MAT=8.0 (tab too narrow)",
    ),
    (
        {"interior_h": 30.0},
        "I-3",
        "interior_h=30 → crossbar mortises at 32mm and 42mm, CROSS_MORT_W=20.1 → ranges overlap",
    ),
]


@pytest.mark.parametrize("kwargs,inv,desc", INVALID_SIZES)
def test_invalid_params_raise_assertion_error(kwargs, inv, desc):
    """make_params() must raise AssertionError for each invalid parameter set."""
    with pytest.raises(AssertionError, match="INVARIANT FAILURES"):
        make_params(**kwargs)
