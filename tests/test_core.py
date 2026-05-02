"""Tests for aridkpi.core — the 5 CORE KPIs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aridkpi.core import (
    ccor,
    energy_climate_sensitivity,
    iod,
    max_thermal_change_rate,
    udh,
)


# ─────────────────────────────────────────────────────────────────────────────
# IOD
# ─────────────────────────────────────────────────────────────────────────────


class TestIOD:
    """Test Indoor Overheating Degree."""

    def test_step_function_analytical(self, step_temperature):
        """8h at 28°C with T_comf=26 ⇒ excess=2 K × 8h = 16 °C·h."""
        result = iod(step_temperature, T_comf=26.0)
        assert pytest.approx(result, abs=1e-6) == 16.0

    def test_no_overheating_returns_zero(self, hourly_24h):
        """All values below threshold ⇒ IOD = 0."""
        T = pd.Series([20.0] * 24, index=hourly_24h)
        assert iod(T, T_comf=26.0) == 0.0

    def test_constant_at_threshold_returns_zero(self, hourly_24h):
        """All values exactly at threshold ⇒ IOD = 0 (positive part operator)."""
        T = pd.Series([26.0] * 24, index=hourly_24h)
        assert iod(T, T_comf=26.0) == 0.0

    def test_with_occupancy_mask(self, step_temperature, hourly_24h):
        """Occupancy mask removes hours from calculation."""
        # First 16 hours unoccupied; only last 8h count
        occ = pd.Series([False] * 16 + [True] * 8, index=hourly_24h)
        # Last 8 h are at 22 °C (below 26) ⇒ IOD = 0
        result = iod(step_temperature, T_comf=26.0, occupancy=occ)
        assert result == 0.0

    def test_with_adaptive_comfort_series(self, hourly_24h):
        """T_comf as a Series (adaptive model)."""
        T = pd.Series([28.0] * 24, index=hourly_24h)
        T_comf = pd.Series([26.0] * 12 + [30.0] * 12, index=hourly_24h)
        # First 12 h: excess = 2 K × 12 h = 24 °C·h
        # Last 12 h: excess = 0
        result = iod(T, T_comf=T_comf)
        assert pytest.approx(result, abs=1e-6) == 24.0

    def test_empty_series_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            iod(pd.Series([], dtype=float, index=pd.DatetimeIndex([])))

    def test_non_datetime_index_raises(self):
        with pytest.raises(TypeError, match="DatetimeIndex"):
            iod(pd.Series([20.0, 28.0]))

    def test_non_series_raises(self):
        with pytest.raises(TypeError, match="pandas Series"):
            iod([20.0, 28.0])  # type: ignore[arg-type]

    def test_all_unoccupied_returns_zero(self, step_temperature, hourly_24h):
        """Edge case: occupancy mask is all False."""
        occ = pd.Series([False] * 24, index=hourly_24h)
        result = iod(step_temperature, T_comf=26.0, occupancy=occ)
        assert result == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CCOR
# ─────────────────────────────────────────────────────────────────────────────


class TestCCOR:
    """Test Climate Change Overheating Resistivity."""

    def test_basic_calculation(self):
        assert ccor(120.0, 80.0, 2.5) == pytest.approx(16.0)

    def test_zero_strategy_effect(self):
        """If the strategy doesn't reduce IOD, CCOR = 0."""
        assert ccor(100.0, 100.0, 2.0) == 0.0

    def test_negative_strategy_makes_it_worse(self):
        """Strategy worse than baseline ⇒ negative CCOR."""
        assert ccor(80.0, 100.0, 2.0) == -10.0

    def test_zero_delta_T_raises(self):
        with pytest.raises(ValueError, match="must be positive"):
            ccor(120.0, 80.0, 0.0)

    def test_negative_delta_T_raises(self):
        with pytest.raises(ValueError, match="must be positive"):
            ccor(120.0, 80.0, -1.0)


# ─────────────────────────────────────────────────────────────────────────────
# UDH
# ─────────────────────────────────────────────────────────────────────────────


class TestUDH:
    """Test Unmet Degree Hours during outage."""

    def test_constant_overheat_72h(self, constant_overheat):
        """72 h at 32 °C with threshold 30 °C ⇒ (32-30) × 72 = 144 °C·h."""
        result = udh(constant_overheat, outage_start="2026-01-15",
                     window="72h", threshold=30.0)
        assert pytest.approx(result, abs=1e-6) == 144.0

    def test_24h_window(self, constant_overheat):
        """Same series but only first 24 h ⇒ 48 °C·h."""
        result = udh(constant_overheat, outage_start="2026-01-15",
                     window="24h", threshold=30.0)
        assert pytest.approx(result, abs=1e-6) == 48.0

    def test_below_threshold_zero(self):
        idx = pd.date_range("2026-01-15", periods=72, freq="h")
        T = pd.Series([28.0] * 72, index=idx)
        assert udh(T, outage_start="2026-01-15", window="72h", threshold=30.0) == 0.0

    def test_window_outside_series_raises(self, constant_overheat):
        with pytest.raises(ValueError, match="does not fit"):
            udh(constant_overheat, outage_start="2026-01-15",
                window="7d", threshold=30.0)

    def test_invalid_window_raises(self, constant_overheat):
        with pytest.raises(KeyError):
            udh(constant_overheat, outage_start="2026-01-15",
                window="48h", threshold=30.0)  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────────────
# energy_climate_sensitivity (ΔE/ΔT)
# ─────────────────────────────────────────────────────────────────────────────


class TestEnergyClimateSensitivity:
    """Test ΔE/ΔT regression."""

    def test_perfect_linear(self):
        """y = 4x + 16 ⇒ slope = 4, R² = 1."""
        df = pd.DataFrame({"T_mean": [16.0, 18.0, 20.0, 22.0],
                           "EUI":    [80.0, 88.0, 96.0, 104.0]})
        r = energy_climate_sensitivity(df)
        assert pytest.approx(r["slope"], abs=1e-9) == 4.0
        assert pytest.approx(r["r_squared"], abs=1e-9) == 1.0
        assert r["n_points"] == 4

    def test_returns_all_keys(self):
        df = pd.DataFrame({"T_mean": [16.0, 18.0, 20.0],
                           "EUI":    [80.0, 90.0, 100.0]})
        r = energy_climate_sensitivity(df)
        assert set(r.keys()) == {"slope", "intercept", "r_squared",
                                 "p_value", "std_err", "n_points"}

    def test_too_few_points_raises(self):
        df = pd.DataFrame({"T_mean": [16.0, 18.0], "EUI": [80.0, 88.0]})
        with pytest.raises(ValueError, match="at least 3"):
            energy_climate_sensitivity(df)

    def test_missing_columns_raises(self):
        df = pd.DataFrame({"X": [1, 2, 3], "Y": [4, 5, 6]})
        with pytest.raises(KeyError):
            energy_climate_sensitivity(df)

    def test_custom_column_names(self):
        df = pd.DataFrame({"temp": [16.0, 18.0, 20.0],
                           "energy": [80.0, 88.0, 96.0]})
        r = energy_climate_sensitivity(df, eui_col="energy", tmean_col="temp")
        assert pytest.approx(r["slope"]) == 4.0


# ─────────────────────────────────────────────────────────────────────────────
# max_thermal_change_rate (dT/dt max)
# ─────────────────────────────────────────────────────────────────────────────


class TestMaxThermalChangeRate:
    """Test dT/dt max."""

    def test_linear_ramp(self, linear_ramp):
        """Slope 1 °C/h ⇒ max |dT/dt| = 1.0."""
        result = max_thermal_change_rate(linear_ramp, smoothing_window=1)
        assert pytest.approx(result, abs=1e-9) == 1.0

    def test_smoothing_attenuates_noise(self):
        """Smoothing reduces the apparent peak rate when noise is present."""
        idx = pd.date_range("2026-01-01", periods=100, freq="h")
        rng = np.random.default_rng(0)
        # Slow trend + high-freq noise
        T = pd.Series(np.linspace(0, 10, 100) + rng.normal(0, 1, 100), index=idx)
        peak_raw = max_thermal_change_rate(T, smoothing_window=1)
        peak_smoothed = max_thermal_change_rate(T, smoothing_window=5)
        assert peak_smoothed < peak_raw

    def test_constant_series_zero_rate(self):
        idx = pd.date_range("2026-01-01", periods=24, freq="h")
        T = pd.Series([22.0] * 24, index=idx)
        assert max_thermal_change_rate(T) == 0.0

    def test_invalid_smoothing_raises(self, linear_ramp):
        with pytest.raises(ValueError, match=">= 1"):
            max_thermal_change_rate(linear_ramp, smoothing_window=0)


# ─────────────────────────────────────────────────────────────────────────────
# Integration / consistency tests — verify that synthetic data + KPI library
# produce sensible results for known typologies
# ─────────────────────────────────────────────────────────────────────────────


class TestTypologyConsistency:
    """Cross-check: synth dataset + KPIs should rank typologies as expected."""

    def test_adobe_has_lower_dT_dt_than_lightweight(self):
        """High thermal mass (adobe) ⇒ slower indoor dynamics ⇒ lower dT/dt max."""
        from aridkpi.synth import synthetic_dataset

        adobe = synthetic_dataset(days=7, typology="adobe", seed=42)
        light = synthetic_dataset(days=7, typology="lightweight", seed=42)
        rate_adobe = max_thermal_change_rate(adobe["T_in"])
        rate_light = max_thermal_change_rate(light["T_in"])
        assert rate_adobe < rate_light, (
            f"Expected adobe ({rate_adobe:.3f}) < lightweight ({rate_light:.3f})"
        )

    def test_lightweight_has_higher_iod_than_adobe(self):
        """Lightweight envelope follows outdoor more closely ⇒ more overheating."""
        from aridkpi.synth import synthetic_dataset

        adobe = synthetic_dataset(days=14, typology="adobe", seed=42)
        light = synthetic_dataset(days=14, typology="lightweight", seed=42)
        iod_adobe = iod(adobe["T_in"], T_comf=26.0)
        iod_light = iod(light["T_in"], T_comf=26.0)
        assert iod_light > iod_adobe, (
            f"Expected lightweight ({iod_light:.2f}) > adobe ({iod_adobe:.2f})"
        )
