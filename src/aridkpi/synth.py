"""
Synthetic data generators for testing and demonstration.

Produces deterministic time series that emulate the typical patterns of
arid-climate residential buildings (high diurnal amplitude, dry summers).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "synthetic_dataset",
    "synthetic_indoor_temperature",
    "synthetic_outdoor_temperature",
    "synthetic_relative_humidity",
]


def synthetic_outdoor_temperature(
    start: str = "2026-01-01",
    days: int = 7,
    freq: str = "10min",
    daily_mean: float = 25.0,
    daily_amplitude: float = 16.0,
    noise_std: float = 0.4,
    seed: int = 42,
) -> pd.Series:
    """Generate a synthetic outdoor temperature series.

    Models a sinusoidal diurnal cycle with peak at 15:00 local time, plus
    Gaussian noise. Default parameters emulate a typical Mendoza summer day:
    mean 25 °C, daily amplitude 16 °C (so range 17–33 °C) — characteristic
    of BWk climate (Köppen-Geiger).

    Parameters
    ----------
    start
        Start timestamp (any pandas-parseable string).
    days
        Number of days to generate.
    freq
        Sampling frequency (default 10 minutes).
    daily_mean
        Mean daily temperature (°C).
    daily_amplitude
        Peak-to-peak diurnal amplitude (°C). 16 °C corresponds to BWk.
    noise_std
        Gaussian noise standard deviation (°C).
    seed
        Random seed for reproducibility.

    Returns
    -------
    pd.Series
        Outdoor temperature in °C indexed by DatetimeIndex.

    Examples
    --------
    >>> T = synthetic_outdoor_temperature(days=1, seed=0)
    >>> int(round(T.mean()))
    25
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start=start, periods=days * 144, freq=freq)
    n = len(idx)
    # Diurnal cycle: peak at 15:00, trough at 03:00
    hours = idx.hour + idx.minute / 60.0
    diurnal = (daily_amplitude / 2.0) * np.sin(2.0 * np.pi * (hours - 9.0) / 24.0)
    noise = rng.normal(0.0, noise_std, n)
    return pd.Series(daily_mean + diurnal + noise, index=idx, name="T_ext")


def synthetic_indoor_temperature(
    T_ext: pd.Series,
    attenuation: float = 0.45,
    phase_lag_hours: float = 4.0,
    indoor_offset: float = 0.0,
) -> pd.Series:
    """Generate a synthetic indoor temperature series from an outdoor series.

    Simulates the effect of envelope thermal mass via two parameters:
    amplitude attenuation and phase lag. Adobe-like envelopes have low
    attenuation values (around 0.2–0.3) and large phase lags (8–12 h).
    Lightweight industrialised envelopes have high attenuation (0.6–0.9) and
    small phase lags (1–3 h).

    Parameters
    ----------
    T_ext
        Outdoor temperature series (°C).
    attenuation
        Indoor amplitude / outdoor amplitude. 0 = perfect attenuation,
        1 = no attenuation. Default 0.45 emulates a typical BWk masonry house.
    phase_lag_hours
        Time lag between outdoor and indoor peaks (hours).
    indoor_offset
        Constant offset added to the indoor temperature (°C). Useful to model
        small heat gains.

    Returns
    -------
    pd.Series
        Indoor temperature series (°C).

    Examples
    --------
    >>> T_ext = synthetic_outdoor_temperature(days=2, seed=0)
    >>> T_in = synthetic_indoor_temperature(T_ext, attenuation=0.3)
    >>> # Indoor amplitude is smaller than outdoor amplitude
    >>> bool(T_in.std() < T_ext.std())
    True
    """
    if not 0.0 <= attenuation <= 1.0:
        raise ValueError(f"attenuation must be in [0, 1], got {attenuation}.")
    if phase_lag_hours < 0:
        raise ValueError(f"phase_lag_hours must be non-negative, got {phase_lag_hours}.")

    daily_mean = float(T_ext.mean())
    deviation = T_ext - daily_mean

    deltas = np.diff(T_ext.index.values).astype("timedelta64[s]").astype(float)
    dt_hours = float(np.median(deltas)) / 3600.0
    lag_steps = round(phase_lag_hours / dt_hours)

    indoor_dev = deviation.shift(lag_steps).fillna(0.0) * attenuation
    return pd.Series(
        daily_mean + indoor_dev.to_numpy() + indoor_offset,
        index=T_ext.index,
        name="T_in",
    )


def synthetic_relative_humidity(
    T_ext: pd.Series,
    daily_mean_rh: float = 35.0,
    rh_amplitude: float = 20.0,
    noise_std: float = 2.0,
    seed: int = 0,
) -> pd.Series:
    """Generate a synthetic outdoor relative humidity series.

    Emulates the typical anti-correlation between RH and temperature in arid
    climates: RH peaks at dawn (when temperature is lowest) and troughs in
    the afternoon. Default parameters reproduce typical Mendoza summer:
    mean 35 %, range 15–55 %.

    Parameters
    ----------
    T_ext
        Outdoor temperature series (used to time the RH cycle).
    daily_mean_rh
        Mean daily RH (%).
    rh_amplitude
        Peak-to-peak amplitude (%).
    noise_std
        Gaussian noise standard deviation (%).
    seed
        Random seed.

    Returns
    -------
    pd.Series
        Relative humidity in % (clipped to [0, 100]).
    """
    rng = np.random.default_rng(seed)
    hours = T_ext.index.hour + T_ext.index.minute / 60.0
    # RH peaks at 06:00, troughs at 18:00 (anti-phase with T)
    diurnal = (rh_amplitude / 2.0) * np.sin(2.0 * np.pi * (hours - 12.0) / 24.0)
    noise = rng.normal(0.0, noise_std, len(T_ext))
    rh = daily_mean_rh + diurnal + noise
    return pd.Series(np.clip(rh, 0.0, 100.0), index=T_ext.index, name="RH_ext")


def synthetic_dataset(
    start: str = "2026-01-15",
    days: int = 14,
    freq: str = "10min",
    typology: str = "masonry_insulated",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a complete synthetic dataset for KPI computation.

    Produces a DataFrame with outdoor T, outdoor RH, indoor T (operative)
    aligned with one of four prototype envelopes:

        * ``"adobe"``                — high mass, low attenuation, large lag
        * ``"masonry_no_insulation"`` — medium mass, medium attenuation
        * ``"masonry_insulated"``    — current Argentine standard (IRAM 11605)
        * ``"lightweight"``          — industrialised, high attenuation, small lag

    Parameters
    ----------
    start
        Start date.
    days
        Number of days.
    freq
        Sampling frequency.
    typology
        One of the four prototypes documented above.
    seed
        Random seed.

    Returns
    -------
    pd.DataFrame
        Columns: ``T_ext``, ``RH_ext``, ``T_in``. DatetimeIndex.

    Examples
    --------
    >>> df = synthetic_dataset(days=3, typology="adobe", seed=0)
    >>> set(df.columns) == {"T_ext", "RH_ext", "T_in"}
    True
    """
    profiles = {
        "adobe":                  {"attenuation": 0.25, "phase_lag_hours": 9.0},
        "masonry_no_insulation":  {"attenuation": 0.55, "phase_lag_hours": 4.0},
        "masonry_insulated":      {"attenuation": 0.40, "phase_lag_hours": 5.0},
        "lightweight":            {"attenuation": 0.80, "phase_lag_hours": 1.5},
    }
    if typology not in profiles:
        raise ValueError(
            f"Unknown typology {typology!r}. Choose one of: {sorted(profiles)}."
        )

    T_ext = synthetic_outdoor_temperature(start=start, days=days, freq=freq, seed=seed)
    RH_ext = synthetic_relative_humidity(T_ext, seed=seed + 1)
    T_in = synthetic_indoor_temperature(T_ext, **profiles[typology])

    return pd.DataFrame({"T_ext": T_ext, "RH_ext": RH_ext, "T_in": T_in})
