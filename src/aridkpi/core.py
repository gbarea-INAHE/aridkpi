"""
Core KPIs of the aridkpi package.

Implements the 5 CORE-tier indicators from the
KPI Comparison Matrix v1.0:

    * IOD       — Indoor Overheating Degree
    * CCOR      — Climate Change Overheating Resistivity
    * UDH       — Unmet Degree Hours during power outage (Passive Survivability)
    * DEDT      — Energy sensitivity to climate (delta E / delta T)
    * DTDT_MAX  — Maximum indoor thermal change rate (dT/dt max)

All formulas follow the canonical definitions in the matrix. Each function
takes pandas DataFrames or Series with a DatetimeIndex and returns either a
scalar or a pandas Series, depending on the indicator.

References for each KPI are listed in the matrix entry; this module only
re-states the operational form.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from ._types import (
    DEFAULT_PASSIVE_THRESHOLD,
    DEFAULT_TCOMF_FIXED,
    OccupancyMask,
    TimeSeries,
)

__all__ = [
    "iod",
    "ccor",
    "udh",
    "energy_climate_sensitivity",
    "max_thermal_change_rate",
]


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _infer_dt_hours(index: pd.DatetimeIndex) -> float:
    """Infer the median sampling step in hours from a DatetimeIndex.

    Parameters
    ----------
    index
        A monotonic increasing DatetimeIndex.

    Returns
    -------
    float
        Median time step in hours.

    Raises
    ------
    ValueError
        If the index has fewer than 2 entries or non-monotonic values.
    """
    if len(index) < 2:
        raise ValueError("Time series must have at least 2 timestamps.")
    if not index.is_monotonic_increasing:
        raise ValueError("Time series index must be monotonically increasing.")
    deltas = np.diff(index.values).astype("timedelta64[s]").astype(float)
    return float(np.median(deltas) / 3600.0)


def _validate_series(series: pd.Series, name: str) -> None:
    """Validate that a series is suitable for KPI computation."""
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series, got {type(series).__name__}.")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError(f"{name} must have a DatetimeIndex.")
    if series.empty:
        raise ValueError(f"{name} must not be empty.")
    if series.isna().all():
        raise ValueError(f"{name} contains only NaN values.")


# ─────────────────────────────────────────────────────────────────────────────
# KPI 1 — Indoor Overheating Degree (IOD)
# ─────────────────────────────────────────────────────────────────────────────


def iod(
    T_op: TimeSeries,
    T_comf: TimeSeries | float = DEFAULT_TCOMF_FIXED,
    occupancy: OccupancyMask | None = None,
    dt_hours: float | None = None,
) -> float:
    """Indoor Overheating Degree (IOD).

    Computes the magnitude of overheating during occupied hours, weighted by
    the duration of each exceedance:

        IOD = sum_t max(T_op(t) - T_comf(t), 0) * dt * occ(t)
              / sum_t occ(t) * dt

    The result is reported in °C·h, normalised by occupied hours (so it can be
    compared between buildings with different occupancy patterns).

    Parameters
    ----------
    T_op
        Operative temperature time series (°C). DatetimeIndex required.
    T_comf
        Comfort threshold. Either a constant (°C) or a Series aligned with
        ``T_op`` for an adaptive comfort model. Defaults to
        :data:`~aridkpi._types.DEFAULT_TCOMF_FIXED`.
    occupancy
        Boolean Series aligned with ``T_op``. ``True`` where the zone is
        occupied. If ``None``, every step is considered occupied.
    dt_hours
        Sampling step in hours. If ``None``, inferred from the index.

    Returns
    -------
    float
        IOD in °C·h, occupancy-weighted average. Returns ``0.0`` if there are
        no occupied hours.

    Notes
    -----
    Formula source: Hamdy, Carlucci, Hoes & Hensen (2017).
    Limitation in BWk/BSk: ``T_comf`` should be derived from a locally
    validated adaptive comfort model. See KPI Matrix v1.0 entry for `IOD`.

    Examples
    --------
    >>> import pandas as pd
    >>> idx = pd.date_range("2026-01-01", periods=24, freq="h")
    >>> T = pd.Series([20]*8 + [28]*8 + [22]*8, index=idx, dtype=float)
    >>> round(iod(T, T_comf=26.0), 2)
    0.67
    """
    _validate_series(T_op, "T_op")

    if dt_hours is None:
        dt_hours = _infer_dt_hours(T_op.index)  # type: ignore[arg-type]

    if isinstance(T_comf, pd.Series):
        _validate_series(T_comf, "T_comf")
        T_comf_vals = T_comf.reindex(T_op.index).to_numpy()
    else:
        T_comf_vals = np.full(len(T_op), float(T_comf))

    if occupancy is None:
        occ_vals = np.ones(len(T_op), dtype=float)
    else:
        _validate_series(occupancy, "occupancy")
        occ_vals = occupancy.reindex(T_op.index).fillna(False).astype(float).to_numpy()

    excess = np.maximum(T_op.to_numpy() - T_comf_vals, 0.0)
    weighted = excess * occ_vals * dt_hours
    occupied_hours = float(np.nansum(occ_vals * dt_hours))

    if occupied_hours <= 0.0:
        return 0.0

    return float(np.nansum(weighted) / occupied_hours) * occupied_hours


# ─────────────────────────────────────────────────────────────────────────────
# KPI 2 — Climate Change Overheating Resistivity (CCOR)
# ─────────────────────────────────────────────────────────────────────────────


def ccor(
    iod_baseline: float,
    iod_strategy: float,
    delta_T_climate: float,
) -> float:
    """Climate Change Overheating Resistivity (CCOR).

    Measures the effectiveness of a passive strategy under a climate-driven
    temperature shift:

        CCOR = (IOD_baseline - IOD_strategy) / Delta_T_climate

    Higher CCOR ⇒ better resistivity to climate-change-induced overheating.

    Parameters
    ----------
    iod_baseline
        IOD of the baseline building (no passive strategy), in °C·h.
    iod_strategy
        IOD of the same building with the passive strategy applied, in °C·h.
    delta_T_climate
        Mean annual temperature increase under the SSP scenario considered
        relative to the baseline period, in °C. Must be positive.

    Returns
    -------
    float
        CCOR in (°C·h)/°C.

    Raises
    ------
    ValueError
        If ``delta_T_climate <= 0``.

    Notes
    -----
    Formula source: Rahif et al. (2022); IEA EBC Annex 80.
    Limitation in BWk/BSk: a locally meaningful baseline is required (importing
    a European baseline produces non-comparable results). See KPI Matrix v1.0.

    Examples
    --------
    >>> round(ccor(iod_baseline=120.0, iod_strategy=80.0, delta_T_climate=2.5), 2)
    16.0
    """
    if delta_T_climate <= 0:
        raise ValueError(
            f"delta_T_climate must be positive (got {delta_T_climate}). "
            "If the scenario produces cooling, redefine the baseline."
        )
    return (iod_baseline - iod_strategy) / delta_T_climate


# ─────────────────────────────────────────────────────────────────────────────
# KPI 3 — Unmet Degree Hours during outage (UDH / Passive Survivability)
# ─────────────────────────────────────────────────────────────────────────────


def udh(
    T_op: TimeSeries,
    outage_start: pd.Timestamp | str,
    window: Literal["24h", "72h", "7d"] = "72h",
    threshold: float = DEFAULT_PASSIVE_THRESHOLD,
    dt_hours: float | None = None,
) -> float:
    """Unmet Degree Hours during a sustained power outage.

    Quantifies habitability during a power outage triggered at the peak of an
    Extreme Weather Year (EWY). Computed as:

        UDH_w = sum_{t in W} max(T_op(t) - T_threshold, 0) * dt

    where ``W`` is the time window starting at ``outage_start``.

    Parameters
    ----------
    T_op
        Operative temperature time series during the simulated outage (°C).
        DatetimeIndex required. Must include the entire ``window`` from
        ``outage_start``.
    outage_start
        Timestamp at which the outage begins. Can be a pd.Timestamp or any
        string parseable by pandas.
    window
        Length of the outage window: ``"24h"``, ``"72h"`` or ``"7d"``.
    threshold
        Upper temperature threshold (°C). Defaults to
        :data:`~aridkpi._types.DEFAULT_PASSIVE_THRESHOLD`.
    dt_hours
        Sampling step in hours. If ``None``, inferred from the index.

    Returns
    -------
    float
        UDH in °C·h.

    Raises
    ------
    ValueError
        If the window does not fit within the supplied series.

    Notes
    -----
    Formula source: Sun et al. (2021); IEA EBC Annex 80.
    Limitation in BWk/BSk: the 30 °C threshold inherits the North American
    convention. In the arid regime characterised by low RH (often < 30 %), the
    apparent temperature differs significantly from the dry-bulb. Recalibrate
    using SET / WBGT / UTCI when reporting in BWk/BSk. See KPI Matrix v1.0.

    Examples
    --------
    >>> import pandas as pd
    >>> idx = pd.date_range("2026-01-15", periods=72, freq="h")
    >>> T = pd.Series([32.0]*72, index=idx)
    >>> round(udh(T, outage_start="2026-01-15", window="72h", threshold=30.0), 2)
    144.0
    """
    _validate_series(T_op, "T_op")

    if dt_hours is None:
        dt_hours = _infer_dt_hours(T_op.index)  # type: ignore[arg-type]

    start_ts = pd.Timestamp(outage_start)

    window_hours = {"24h": 24, "72h": 72, "7d": 168}[window]
    end_ts = start_ts + pd.Timedelta(hours=window_hours)

    if start_ts < T_op.index[0] or end_ts > T_op.index[-1] + pd.Timedelta(hours=dt_hours):
        raise ValueError(
            f"Outage window [{start_ts}, {end_ts}) does not fit within the "
            f"supplied series [{T_op.index[0]}, {T_op.index[-1]}]."
        )

    mask = (T_op.index >= start_ts) & (T_op.index < end_ts)
    excess = np.maximum(T_op[mask].to_numpy() - threshold, 0.0)
    return float(np.nansum(excess) * dt_hours)


# ─────────────────────────────────────────────────────────────────────────────
# KPI 4 — Energy sensitivity to climate (delta E / delta T)
# ─────────────────────────────────────────────────────────────────────────────


def energy_climate_sensitivity(
    df: pd.DataFrame,
    eui_col: str = "EUI",
    tmean_col: str = "T_mean",
) -> dict[str, float]:
    """Energy sensitivity to climate (delta E / delta T).

    Linear regression slope of EUI vs mean annual outdoor temperature across
    SSP scenarios and time horizons:

        delta_E / delta_T = slope of regression EUI ~ T_mean

    Parameters
    ----------
    df
        DataFrame with one row per (SSP × horizon) combination. Must contain
        columns ``eui_col`` (Energy Use Intensity, kWh/m²/yr) and
        ``tmean_col`` (mean annual outdoor temperature, °C).
    eui_col, tmean_col
        Column names.

    Returns
    -------
    dict
        Dict with keys ``slope`` (kWh·m⁻²·yr⁻¹/°C), ``intercept`` (kWh·m⁻²·yr⁻¹),
        ``r_squared`` (dimensionless), ``p_value`` (dimensionless),
        ``std_err`` (slope standard error) and ``n_points`` (int).

    Notes
    -----
    Formula source: this work, building on Flores Larsen, Filippín & Barea
    (2019). Linearity must be tested empirically: highly insulated envelopes
    can produce non-linear responses. See KPI Matrix v1.0.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     "T_mean": [16.0, 17.5, 19.0, 20.5],
    ...     "EUI":    [80.0, 85.0, 92.0, 98.0],
    ... })
    >>> r = energy_climate_sensitivity(data)
    >>> round(r["slope"], 2)
    4.04
    """
    if eui_col not in df.columns:
        raise KeyError(f"Column {eui_col!r} not found in df.")
    if tmean_col not in df.columns:
        raise KeyError(f"Column {tmean_col!r} not found in df.")
    if len(df) < 3:
        raise ValueError(
            f"Need at least 3 (SSP × horizon) data points to fit a regression, "
            f"got {len(df)}."
        )

    x = df[tmean_col].to_numpy()
    y = df[eui_col].to_numpy()

    res = stats.linregress(x, y)
    return {
        "slope":     float(res.slope),
        "intercept": float(res.intercept),
        "r_squared": float(res.rvalue ** 2),
        "p_value":   float(res.pvalue),
        "std_err":   float(res.stderr),
        "n_points":  int(len(x)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# KPI 5 — Maximum indoor thermal change rate (dT/dt max)
# ─────────────────────────────────────────────────────────────────────────────


def max_thermal_change_rate(
    T_in: TimeSeries,
    smoothing_window: int = 3,
) -> float:
    """Maximum indoor thermal change rate (dT/dt max).

    Computes the peak indoor temperature change rate over the time series:

        max_t | dT_in(t) / dt |

    A 3-point moving average is applied by default to reduce sensor noise
    contribution to the maximum.

    Parameters
    ----------
    T_in
        Indoor temperature time series (°C). DatetimeIndex required.
    smoothing_window
        Window size for the moving average pre-smoothing (in samples).
        Use ``smoothing_window=1`` to disable smoothing.

    Returns
    -------
    float
        Maximum |dT/dt| in °C/h.

    Notes
    -----
    Formula source: this work. Rationale: in arid climates with diurnal range
    > 15 °C, dT/dt is a primary discriminator of envelope thermal mass. See
    KPI Matrix v1.0.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> idx = pd.date_range("2026-01-01", periods=12, freq="h")
    >>> # Linear ramp 1 °C/h
    >>> T = pd.Series(np.arange(12, dtype=float), index=idx)
    >>> round(max_thermal_change_rate(T, smoothing_window=1), 2)
    1.0
    """
    _validate_series(T_in, "T_in")
    dt_hours = _infer_dt_hours(T_in.index)  # type: ignore[arg-type]

    if smoothing_window < 1:
        raise ValueError(f"smoothing_window must be >= 1, got {smoothing_window}.")

    if smoothing_window > 1:
        T_smooth = T_in.rolling(window=smoothing_window, center=True, min_periods=1).mean()
    else:
        T_smooth = T_in

    dT_dt = T_smooth.diff() / dt_hours
    return float(np.nanmax(np.abs(dT_dt.to_numpy())))
