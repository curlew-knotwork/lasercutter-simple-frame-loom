"""
tests/test_sanity.py — Multi-size end-to-end generation test.

NOT run in normal pytest (excluded by addopts = -m "not sanity" in pytest.ini).
Run explicitly:
    .venv/bin/python3 -m pytest -m sanity tests/test_sanity.py -v

Three loom sizes are generated and fully verified:
  small      200×280mm  21 notches  (common small weaving project size)
  medium     300×400mm  31 notches  (default, also used in regular tests)
  wide       400×400mm  41 notches  (twice the width and thread count of small)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.params import make_params
import src.loom  as loom_mod
import src.box   as box_mod
import src.stand as stand_mod

# (interior_w, interior_h, notch_pitch, label)
SIZES = [
    (200, 280, 10, "small   200×280mm  21 notches"),
    (300, 400, 10, "medium  300×400mm  31 notches  [default]"),
    (400, 400, 10, "wide    400×400mm  41 notches"),
]


@pytest.mark.sanity
@pytest.mark.parametrize("iw,ih,pitch,label", SIZES, ids=["small","medium","wide"])
def test_loom_generates_and_verifies(iw, ih, pitch, label):
    """loom.layout() + verify() pass for every size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch)
    placed = loom_mod.layout(p)
    results = loom_mod.verify(placed, p)
    failures = [(name, msg) for name, ok, msg in results if not ok]
    assert not failures, f"{label}: loom verify failures: {failures}"


@pytest.mark.sanity
@pytest.mark.parametrize("iw,ih,pitch,label", SIZES, ids=["small","medium","wide"])
def test_box_generates_and_verifies(iw, ih, pitch, label):
    """box.layout() + verify() pass for every size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch)
    placed = box_mod.layout(p)
    results = box_mod.verify(placed, p)
    failures = [(name, msg) for name, ok, msg in results if not ok]
    assert not failures, f"{label}: box verify failures: {failures}"


@pytest.mark.sanity
@pytest.mark.parametrize("iw,ih,pitch,label", SIZES, ids=["small","medium","wide"])
def test_stand_generates_and_verifies(iw, ih, pitch, label):
    """stand.layout() + verify() pass for every size."""
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch)
    placed = stand_mod.layout(p)
    results = stand_mod.verify(placed, p)
    failures = [(name, msg) for name, ok, msg in results if not ok]
    assert not failures, f"{label}: stand verify failures: {failures}"


@pytest.mark.sanity
@pytest.mark.parametrize("iw,ih,pitch,label", SIZES, ids=["small","medium","wide"])
def test_write_all_modules(iw, ih, pitch, label):
    """write() produces inspectable SVGs in output/sanity/<size>/ for all three modules."""
    import pathlib
    size_id = label.split()[0]   # "small", "medium", "wide"
    out_dir = pathlib.Path("output/sanity") / size_id
    out_dir.mkdir(parents=True, exist_ok=True)
    p = make_params(interior_w=iw, interior_h=ih, notch_pitch=pitch)
    loom_path  = loom_mod.write(p,  str(out_dir / "loom.svg"))
    box_path   = box_mod.write(p,   str(out_dir / "optional_box.svg"))
    stand_path = stand_mod.write(p, str(out_dir / "optional_loom_stand.svg"))
    for path in (loom_path, box_path, stand_path):
        assert os.path.exists(path), f"{label}: output file missing: {path}"
    print(f"\n  {label}: SVGs written to {out_dir}/")
