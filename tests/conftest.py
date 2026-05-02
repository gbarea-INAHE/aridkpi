"""Shared fixtures for the aridkpi test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make `import aridkpi` work without prior installation, both locally and in CI.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def hourly_24h() -> pd.DatetimeIndex:
    """24 hourly timestamps starting 2026-01-01 00:00."""
    return pd.date_range("2026-01-01", periods=24, freq="h")


@pytest.fixture
def step_temperature(hourly_24h: pd.DatetimeIndex) -> pd.Series:
    """Step function: 8h cool, 8h hot, 8h cool. Used for IOD analytics tests."""
    return pd.Series([20.0] * 8 + [28.0] * 8 + [22.0] * 8, index=hourly_24h)


@pytest.fixture
def constant_overheat() -> pd.Series:
    """72 hourly samples at constant 32 °C."""
    idx = pd.date_range("2026-01-15", periods=72, freq="h")
    return pd.Series([32.0] * 72, index=idx)


@pytest.fixture
def linear_ramp() -> pd.Series:
    """Linear ramp 0..11 °C with 1-hour steps. dT/dt = 1.0 °C/h exactly."""
    idx = pd.date_range("2026-01-01", periods=12, freq="h")
    return pd.Series(np.arange(12, dtype=float), index=idx)
