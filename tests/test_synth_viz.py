"""Tests for aridkpi.synth and aridkpi.viz."""

from __future__ import annotations

import pandas as pd
import pytest

from aridkpi.synth import (
    synthetic_dataset,
    synthetic_indoor_temperature,
    synthetic_outdoor_temperature,
    synthetic_relative_humidity,
)


class TestSyntheticOutdoor:
    def test_default_params(self):
        s = synthetic_outdoor_temperature(days=2, seed=0)
        # 2 days × 144 samples/day at 10-min freq
        assert len(s) == 288
        assert isinstance(s.index, pd.DatetimeIndex)

    def test_mean_close_to_target(self):
        s = synthetic_outdoor_temperature(days=14, daily_mean=25.0, seed=0)
        # Allow ±0.3 °C tolerance for finite sampling and noise
        assert abs(s.mean() - 25.0) < 0.3

    def test_amplitude_emerges(self):
        s = synthetic_outdoor_temperature(days=3, daily_amplitude=16.0, seed=0)
        # Daily range should be at least 12 °C (some attenuation by sampling)
        daily_range = s.max() - s.min()
        assert daily_range > 12.0


class TestSyntheticIndoor:
    def test_attenuation_reduces_amplitude(self):
        T_ext = synthetic_outdoor_temperature(days=3, seed=0)
        T_in_low = synthetic_indoor_temperature(T_ext, attenuation=0.2)
        T_in_high = synthetic_indoor_temperature(T_ext, attenuation=0.9)
        # Higher attenuation parameter ⇒ closer to outdoor amplitude
        assert T_in_low.std() < T_in_high.std()

    def test_invalid_attenuation_raises(self):
        T_ext = synthetic_outdoor_temperature(days=1, seed=0)
        with pytest.raises(ValueError, match="must be in"):
            synthetic_indoor_temperature(T_ext, attenuation=1.5)

    def test_invalid_phase_lag_raises(self):
        T_ext = synthetic_outdoor_temperature(days=1, seed=0)
        with pytest.raises(ValueError, match="non-negative"):
            synthetic_indoor_temperature(T_ext, phase_lag_hours=-1.0)


class TestSyntheticRH:
    def test_clipped_to_valid_range(self):
        T_ext = synthetic_outdoor_temperature(days=3, seed=0)
        rh = synthetic_relative_humidity(T_ext, daily_mean_rh=10.0, rh_amplitude=40.0)
        assert rh.min() >= 0.0
        assert rh.max() <= 100.0


class TestSyntheticDataset:
    def test_columns_present(self):
        df = synthetic_dataset(days=3, typology="masonry_insulated", seed=0)
        assert set(df.columns) == {"T_ext", "RH_ext", "T_in"}

    def test_invalid_typology_raises(self):
        with pytest.raises(ValueError, match="Unknown typology"):
            synthetic_dataset(typology="banana")  # type: ignore[arg-type]

    def test_all_typologies_work(self):
        for typology in ["adobe", "masonry_no_insulation",
                         "masonry_insulated", "lightweight"]:
            df = synthetic_dataset(days=2, typology=typology, seed=0)
            assert len(df) > 0

    def test_reproducibility(self):
        df1 = synthetic_dataset(days=2, seed=42)
        df2 = synthetic_dataset(days=2, seed=42)
        pd.testing.assert_frame_equal(df1, df2)


# ─────────────────────────────────────────────────────────────────────────────
# viz tests — only run if matplotlib is available
# ─────────────────────────────────────────────────────────────────────────────


_matplotlib_available = False
try:
    import matplotlib  # noqa: F401
    _matplotlib_available = True
except ImportError:
    pass


@pytest.mark.skipif(not _matplotlib_available, reason="matplotlib not installed")
class TestViz:
    def test_plot_temperature_returns_axes(self):
        import matplotlib

        matplotlib.use("Agg")  # headless
        from aridkpi.viz import plot_temperature_series

        df = synthetic_dataset(days=2, seed=0)
        ax = plot_temperature_series(df["T_in"], df["T_ext"])
        assert ax is not None

    def test_plot_overheating_returns_axes(self):
        import matplotlib

        matplotlib.use("Agg")
        from aridkpi.viz import plot_overheating_diagnostic

        df = synthetic_dataset(days=2, typology="lightweight", seed=0)
        ax = plot_overheating_diagnostic(df["T_in"], T_comf=26.0)
        assert ax is not None

    def test_plot_kpi_summary_returns_axes(self):
        import matplotlib

        matplotlib.use("Agg")
        from aridkpi.viz import plot_kpi_summary

        data = {"adobe":       {"IOD": 45.0, "dT_dt_max": 0.6},
                "lightweight": {"IOD": 92.0, "dT_dt_max": 2.4}}
        ax = plot_kpi_summary(data)
        assert ax is not None

    def test_plot_kpi_summary_empty_raises(self):
        from aridkpi.viz import plot_kpi_summary

        with pytest.raises(ValueError, match="empty"):
            plot_kpi_summary({})
