"""
Data loaders for common monitoring and simulation file formats.

Currently supported:

    * HOBO MX series CSV (Onset)
    * Generic CSV with timestamp + temperature columns
    * EnergyPlus .eso/.csv output (zone mean air temperature)
    * Pre-aggregated DataFrame validation (``ensure_valid``)

All loaders return a pandas Series or DataFrame with a tz-naive
DatetimeIndex sorted in ascending order. NaN values are preserved (use
``ensure_valid`` to validate before computing KPIs).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

__all__ = [
    "ensure_valid",
    "load_energyplus_csv",
    "load_generic_csv",
    "load_hobo_csv",
]


def _to_naive(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Strip timezone info if present, returning a tz-naive index."""
    if idx.tz is not None:
        return idx.tz_localize(None)
    return idx


def load_hobo_csv(
    path: str | Path,
    timestamp_col: str = "Date Time",
    temperature_col: str | None = None,
    rh_col: str | None = None,
    skiprows: int = 1,
) -> pd.DataFrame:
    """Load a HOBO MX-series CSV exported by Onset HOBOware / HOBOconnect.

    HOBO CSVs typically have a 1-line header above the column names. The
    timestamp is parsed automatically. Temperature and RH columns can be
    provided explicitly or auto-detected by name fragment.

    Parameters
    ----------
    path
        Path to the CSV.
    timestamp_col
        Name of the timestamp column.
    temperature_col
        Name of the temperature column. If ``None``, the first column whose
        name contains "Temp" (case-insensitive) is used.
    rh_col
        Name of the RH column. If ``None``, the first column whose name
        contains "RH" or "Humidity" is used (or no RH if none found).
    skiprows
        Number of metadata rows to skip before the header (HOBO default = 1).

    Returns
    -------
    pd.DataFrame
        Columns ``T`` (and optionally ``RH``), DatetimeIndex.

    Raises
    ------
    FileNotFoundError, KeyError
        Standard pandas exceptions if the file or columns are not found.
    """
    path = Path(path)
    df_raw = pd.read_csv(path, skiprows=skiprows)
    {c.lower(): c for c in df_raw.columns}

    if timestamp_col not in df_raw.columns:
        # try a tolerant match
        for c in df_raw.columns:
            if "date" in c.lower() and "time" in c.lower():
                timestamp_col = c
                break
        else:
            raise KeyError(
                f"Timestamp column {timestamp_col!r} not found. "
                f"Available columns: {list(df_raw.columns)}"
            )

    if temperature_col is None:
        for c in df_raw.columns:
            if "temp" in c.lower():
                temperature_col = c
                break
        else:
            raise KeyError(
                "No temperature column auto-detected. Pass temperature_col explicitly."
            )

    if rh_col is None:
        for c in df_raw.columns:
            cl = c.lower()
            if "rh" in cl or "humidity" in cl:
                rh_col = c
                break

    timestamps = pd.to_datetime(df_raw[timestamp_col])
    out_data: dict[str, pd.Series] = {"T": pd.to_numeric(df_raw[temperature_col], errors="coerce")}
    if rh_col is not None:
        out_data["RH"] = pd.to_numeric(df_raw[rh_col], errors="coerce")

    df = pd.DataFrame(out_data)
    df.index = _to_naive(pd.DatetimeIndex(timestamps))
    df = df.sort_index()
    df.index.name = "timestamp"
    return df


def load_generic_csv(
    path: str | Path,
    timestamp_col: str = "timestamp",
    columns: Iterable[str] | None = None,
    parse_kwargs: dict | None = None,
) -> pd.DataFrame:
    """Load any CSV with a timestamp column and one or more numeric columns.

    Parameters
    ----------
    path
        Path to the CSV.
    timestamp_col
        Name of the timestamp column.
    columns
        Iterable of column names to keep besides the timestamp. If ``None``,
        all numeric columns are kept.
    parse_kwargs
        Extra keyword arguments forwarded to ``pandas.read_csv``.

    Returns
    -------
    pd.DataFrame
        DataFrame with the requested columns indexed by DatetimeIndex.
    """
    path = Path(path)
    parse_kwargs = parse_kwargs or {}
    df = pd.read_csv(path, **parse_kwargs)

    if timestamp_col not in df.columns:
        raise KeyError(f"Timestamp column {timestamp_col!r} not found in {path}.")

    df.index = _to_naive(pd.DatetimeIndex(pd.to_datetime(df[timestamp_col])))
    df = df.drop(columns=[timestamp_col])

    if columns is not None:
        cols = list(columns)
        missing = set(cols) - set(df.columns)
        if missing:
            raise KeyError(f"Columns not found: {sorted(missing)}.")
        df = df[cols]
    else:
        df = df.select_dtypes(include="number")

    df = df.sort_index()
    df.index.name = "timestamp"
    return df


def load_energyplus_csv(
    path: str | Path,
    zone_air_temp_col: str | None = None,
    operative_temp_col: str | None = None,
) -> pd.DataFrame:
    """Load an EnergyPlus .csv output (eplusout.csv).

    EnergyPlus reports timestamps in the form ``MM/DD HH:MM:SS`` for the
    Date/Time column. We assume the simulation year is the current year unless
    embedded in the column name, which EnergyPlus does not do by default.

    Parameters
    ----------
    path
        Path to the EnergyPlus CSV.
    zone_air_temp_col
        Substring used to match the zone mean air temperature column. If
        ``None``, auto-detected by matching ``"Zone Mean Air Temperature"``.
    operative_temp_col
        Substring used to match the zone operative temperature column. If
        ``None``, auto-detected by matching ``"Zone Operative Temperature"``.

    Returns
    -------
    pd.DataFrame
        Columns ``T_air`` and/or ``T_op``. DatetimeIndex.

    Notes
    -----
    EnergyPlus timestamps use 24:00:00 to denote midnight at the end of the
    day. We map this to 00:00:00 of the next day before parsing.
    """
    path = Path(path)
    df_raw = pd.read_csv(path)
    if "Date/Time" not in df_raw.columns:
        raise KeyError(
            f"'Date/Time' column not found in {path}. "
            "Is this an EnergyPlus CSV output?"
        )

    # Fix the 24:00:00 quirk
    def _fix(ts: str) -> str:
        ts = ts.strip()
        if " 24:00:00" in ts:
            ts = ts.replace(" 24:00:00", " 00:00:00")
        return ts

    raw_dates = df_raw["Date/Time"].astype(str).map(_fix)
    # EnergyPlus default format: " MM/DD  HH:MM:SS"
    parsed = pd.to_datetime(raw_dates, format="%m/%d %H:%M:%S", errors="coerce")
    if parsed.isna().all():
        # try with leading whitespace stripped automatically by pandas
        parsed = pd.to_datetime(raw_dates, errors="coerce")

    out: dict[str, pd.Series] = {}

    if operative_temp_col is None:
        for c in df_raw.columns:
            if "Zone Operative Temperature" in c:
                operative_temp_col = c
                break
    if operative_temp_col is not None and operative_temp_col in df_raw.columns:
        out["T_op"] = pd.to_numeric(df_raw[operative_temp_col], errors="coerce")

    if zone_air_temp_col is None:
        for c in df_raw.columns:
            if "Zone Mean Air Temperature" in c:
                zone_air_temp_col = c
                break
    if zone_air_temp_col is not None and zone_air_temp_col in df_raw.columns:
        out["T_air"] = pd.to_numeric(df_raw[zone_air_temp_col], errors="coerce")

    if not out:
        raise KeyError(
            "Neither 'Zone Operative Temperature' nor 'Zone Mean Air Temperature' "
            f"found in {path}. Available columns: {list(df_raw.columns)}"
        )

    df = pd.DataFrame(out)
    df.index = _to_naive(pd.DatetimeIndex(parsed))
    df = df.sort_index()
    df.index.name = "timestamp"
    return df


def ensure_valid(
    series: pd.Series,
    *,
    name: str = "series",
    require_monotonic: bool = True,
    max_gap_minutes: float | None = None,
) -> None:
    """Run sanity checks on a time series before KPI computation.

    Raises a ValueError with an informative message if any check fails. Does
    not modify the series.

    Parameters
    ----------
    series
        The series to validate.
    name
        Display name for error messages.
    require_monotonic
        If ``True``, fail when the index is not strictly increasing.
    max_gap_minutes
        If set, fail when any gap between consecutive timestamps exceeds this
        threshold (minutes). Useful for detecting unflagged outages.
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series, got {type(series).__name__}.")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError(f"{name}: index must be a DatetimeIndex.")
    if series.empty:
        raise ValueError(f"{name} is empty.")
    if require_monotonic and not series.index.is_monotonic_increasing:
        raise ValueError(f"{name}: index is not strictly increasing.")
    if series.isna().all():
        raise ValueError(f"{name} contains only NaN values.")
    if max_gap_minutes is not None and len(series) > 1:
        gaps = pd.Series(series.index).diff().dt.total_seconds() / 60.0
        max_gap = float(gaps.max())
        if max_gap > max_gap_minutes:
            raise ValueError(
                f"{name}: largest gap is {max_gap:.1f} min, exceeds "
                f"max_gap_minutes={max_gap_minutes:.1f}."
            )
