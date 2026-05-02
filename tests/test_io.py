"""Tests for aridkpi.io — data loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from aridkpi.io import (
    ensure_valid,
    load_energyplus_csv,
    load_generic_csv,
    load_hobo_csv,
)


@pytest.fixture
def hobo_csv(tmp_path: Path) -> Path:
    """Write a minimal HOBO-like CSV to a temporary path.

    Note: ``encoding="utf-8"`` is required for cross-platform consistency.
    On Linux/macOS, ``Path.write_text`` defaults to UTF-8; on Windows it
    defaults to the system codepage (cp1252), which silently corrupts the
    ``°`` character — and pandas' ``read_csv`` always assumes UTF-8 by
    default. Forcing UTF-8 on the write side keeps the test deterministic.
    """
    p = tmp_path / "hobo.csv"
    p.write_text(
        '"Plot Title: Test Logger"\n'
        '"#","Date Time","Temp (°C)","RH (%)"\n'
        '1,"2026-01-01 00:00:00",22.5,40.1\n'
        '2,"2026-01-01 00:10:00",22.7,39.8\n'
        '3,"2026-01-01 00:20:00",22.9,39.5\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def generic_csv(tmp_path: Path) -> Path:
    p = tmp_path / "data.csv"
    p.write_text(
        "timestamp,T_in,T_ext\n"
        "2026-01-01 00:00:00,22.5,15.0\n"
        "2026-01-01 01:00:00,22.6,14.5\n"
        "2026-01-01 02:00:00,22.4,14.0\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def energyplus_csv(tmp_path: Path) -> Path:
    p = tmp_path / "eplusout.csv"
    p.write_text(
        "Date/Time,LIVING:Zone Operative Temperature [C](Hourly),"
        "LIVING:Zone Mean Air Temperature [C](Hourly)\n"
        " 01/01  01:00:00,22.5,22.4\n"
        " 01/01  02:00:00,22.7,22.6\n"
        " 01/01  03:00:00,22.9,22.8\n",
        encoding="utf-8",
    )
    return p


class TestLoadHoboCsv:
    def test_basic_load(self, hobo_csv: Path):
        df = load_hobo_csv(hobo_csv)
        assert "T" in df.columns
        assert "RH" in df.columns
        assert len(df) == 3
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.is_monotonic_increasing

    def test_temperature_values(self, hobo_csv: Path):
        df = load_hobo_csv(hobo_csv)
        assert df["T"].iloc[0] == pytest.approx(22.5)
        assert df["T"].iloc[1] == pytest.approx(22.7)


class TestLoadGenericCsv:
    def test_basic_load(self, generic_csv: Path):
        df = load_generic_csv(generic_csv)
        assert set(df.columns) >= {"T_in", "T_ext"}
        assert len(df) == 3

    def test_select_columns(self, generic_csv: Path):
        df = load_generic_csv(generic_csv, columns=["T_in"])
        assert list(df.columns) == ["T_in"]

    def test_missing_timestamp_raises(self, tmp_path: Path):
        p = tmp_path / "bad.csv"
        p.write_text("date,T\n2026-01-01,22.5\n", encoding="utf-8")
        with pytest.raises(KeyError, match="timestamp"):
            load_generic_csv(p)


class TestLoadEnergyplusCsv:
    def test_basic_load(self, energyplus_csv: Path):
        df = load_energyplus_csv(energyplus_csv)
        assert "T_op" in df.columns
        assert "T_air" in df.columns
        assert len(df) == 3


class TestEnsureValid:
    def test_passes_for_clean_series(self):
        idx = pd.date_range("2026-01-01", periods=24, freq="h")
        s = pd.Series(range(24), index=idx, dtype=float)
        ensure_valid(s)  # Should not raise

    def test_fails_for_non_series(self):
        with pytest.raises(TypeError, match="pandas Series"):
            ensure_valid([1, 2, 3])  # type: ignore[arg-type]

    def test_fails_for_empty(self):
        s = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
        with pytest.raises(ValueError, match="empty"):
            ensure_valid(s)

    def test_fails_for_all_nan(self):
        idx = pd.date_range("2026-01-01", periods=3, freq="h")
        s = pd.Series([float("nan")] * 3, index=idx)
        with pytest.raises(ValueError, match="NaN"):
            ensure_valid(s)

    def test_max_gap_detection(self):
        idx = pd.DatetimeIndex(["2026-01-01 00:00", "2026-01-01 00:10",
                                "2026-01-01 02:00"])  # 110-min gap
        s = pd.Series([1.0, 2.0, 3.0], index=idx)
        with pytest.raises(ValueError, match="largest gap"):
            ensure_valid(s, max_gap_minutes=30.0)

    def test_max_gap_allows_within_tolerance(self):
        idx = pd.DatetimeIndex(["2026-01-01 00:00", "2026-01-01 00:10",
                                "2026-01-01 00:20"])
        s = pd.Series([1.0, 2.0, 3.0], index=idx)
        ensure_valid(s, max_gap_minutes=15.0)  # passes
