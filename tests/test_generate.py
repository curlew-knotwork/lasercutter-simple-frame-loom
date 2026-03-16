"""
tests/test_generate.py — Tests for src/generate.py CLI entry point (D-29).
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestGenerateCLI:

    def test_run_default_returns_zero(self):
        """run() with 300×400mm, 5mm pitch, min_tooth_w=2.0 (opt-out of 4mm ply floor) returns 0."""
        from src.generate import run
        rc = run(300.0, 400.0, 5.0, 6.0, 0.15, min_tooth_w=2.0)
        assert rc == 0

    def test_run_small_returns_zero(self):
        """run() with 150×200mm, 5mm pitch, min_tooth_w=2.0 returns 0."""
        from src.generate import run
        rc = run(150.0, 200.0, 5.0, 6.0, 0.15, min_tooth_w=2.0)
        assert rc == 0

    def test_run_chunky_pitch_returns_zero(self):
        """run() with 300×400mm, 10mm pitch returns 0 (success)."""
        from src.generate import run
        rc = run(300.0, 400.0, 10.0, 6.0, 0.15)
        assert rc == 0

    def test_run_invalid_width_too_small_returns_one(self):
        """run() with interior_w=100 (< 150) returns 1 (failure)."""
        from src.generate import run
        rc = run(100.0, 400.0, 5.0, 6.0, 0.15)
        assert rc == 1

    def test_run_invalid_height_too_large_returns_one(self):
        """run() with interior_h=600 (> 550) returns 1 (failure)."""
        from src.generate import run
        rc = run(300.0, 600.0, 5.0, 6.0, 0.15)
        assert rc == 1

    def test_run_invalid_pitch_not_divisible_returns_one(self):
        """run() with interior_w=293 not divisible by pitch=5 returns 1."""
        from src.generate import run
        rc = run(293.0, 400.0, 5.0, 6.0, 0.15)
        assert rc == 1

    def test_run_invalid_mat_returns_one(self):
        """run() with mat=8.0 violates I-5 (TAB_W < MAT), returns 1."""
        from src.generate import run
        rc = run(300.0, 400.0, 5.0, 8.0, 0.15)
        assert rc == 1
