"""
Shared type aliases and constants for aridkpi.

Reusing these aliases keeps the public API consistent and makes future
refactoring (e.g. switching to xarray) a one-line change.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

import pandas as pd

# Public type aliases ─────────────────────────────────────────────────────────
TimeSeries: TypeAlias = pd.Series
"""A pandas Series indexed by a DatetimeIndex with monotonic increasing values."""

OccupancyMask: TypeAlias = pd.Series
"""A boolean pandas Series aligned with a TimeSeries, True where occupied."""

# Sub-hourly time step in seconds
DEFAULT_DT_SECONDS = 600
"""Default sampling step assumed if not inferred: 10 minutes (600 s)."""

# Threshold conventions ───────────────────────────────────────────────────────
DEFAULT_TCOMF_FIXED = 26.0
"""Default fixed comfort threshold (°C) used when no adaptive model is supplied.

Aligned with EN 16798-1:2019 category II upper limit for free-running buildings
in summer. Should be replaced by a locally-validated adaptive model in BWk/BSk.
"""

DEFAULT_PASSIVE_THRESHOLD = 30.0
"""Default upper threshold (°C) for Passive Survivability (UDH) calculation.

This threshold inherits the North American convention documented in
Sun et al. (2021). For BWk/BSk it should be recalibrated using SET (Standard
Effective Temperature) accounting for low relative humidity. See the KPI
Comparison Matrix v1.0 for the full discussion.
"""

# SSP scenarios supported by aridkpi.core.energy_climate_sensitivity ──────────
SSPScenario: TypeAlias = Literal["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]

# KPI tier identifiers ─────────────────────────────────────────────────────
Tier: TypeAlias = Literal["CORE", "EXTENSION", "EXPLORATORY"]
