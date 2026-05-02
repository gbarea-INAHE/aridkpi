"""
Visualisation utilities for aridkpi.

All functions are import-guarded for matplotlib so the core package can be
installed without it. Use ``pip install aridkpi[viz]`` to enable.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ._types import DEFAULT_TCOMF_FIXED

__all__ = [
    "plot_temperature_series",
    "plot_overheating_diagnostic",
    "plot_kpi_summary",
]


def _require_matplotlib() -> Any:
    """Import matplotlib lazily to keep it as an optional dependency."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "matplotlib is required for aridkpi.viz. "
            "Install with: pip install aridkpi[viz]"
        ) from exc
    return plt


def plot_temperature_series(
    T_in: pd.Series,
    T_ext: pd.Series | None = None,
    T_comf: float = DEFAULT_TCOMF_FIXED,
    title: str = "Indoor / outdoor temperature",
    ax: Any | None = None,
):
    """Plot indoor (and optional outdoor) temperature with comfort threshold.

    Parameters
    ----------
    T_in
        Indoor temperature series.
    T_ext
        Optional outdoor temperature series (overlaid on the same axes).
    T_comf
        Comfort threshold drawn as a horizontal reference line.
    title
        Plot title.
    ax
        Optional matplotlib axes. If ``None``, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
        The axes used.
    """
    plt = _require_matplotlib()
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    if T_ext is not None:
        ax.plot(T_ext.index, T_ext.to_numpy(),
                color="#9ca3af", linewidth=0.8, label="Outdoor")
    ax.plot(T_in.index, T_in.to_numpy(),
            color="#1f4e79", linewidth=1.4, label="Indoor")
    ax.axhline(T_comf, color="#c0392b", linestyle="--", linewidth=1.0,
               label=f"Comfort threshold ({T_comf} °C)")

    ax.set_title(title)
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    return ax


def plot_overheating_diagnostic(
    T_op: pd.Series,
    T_comf: float = DEFAULT_TCOMF_FIXED,
    title: str = "Overheating diagnostic",
    ax: Any | None = None,
):
    """Visual diagnostic of overheating: shaded area = excess over T_comf.

    Useful for explaining IOD intuitively: the shaded area under the curve
    above the threshold is exactly the IOD integral.

    Parameters
    ----------
    T_op
        Operative temperature series.
    T_comf
        Comfort threshold.
    title
        Plot title.
    ax
        Optional matplotlib axes.

    Returns
    -------
    matplotlib.axes.Axes
        The axes used.
    """
    plt = _require_matplotlib()
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    t = T_op.index
    y = T_op.to_numpy()

    ax.plot(t, y, color="#1f4e79", linewidth=1.2, label="T_op")
    ax.axhline(T_comf, color="#c0392b", linestyle="--", linewidth=1.0,
               label=f"T_comf = {T_comf} °C")
    ax.fill_between(t, T_comf, y, where=(y > T_comf),
                    interpolate=True, color="#c0392b", alpha=0.25,
                    label="Overheating excess")

    ax.set_title(title)
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    return ax


def plot_kpi_summary(
    kpi_results: dict[str, dict[str, float]],
    title: str = "KPI summary across typologies",
    ax: Any | None = None,
):
    """Bar chart comparing KPI values across typologies / cases.

    Parameters
    ----------
    kpi_results
        Nested dict of the form ``{case_name: {kpi_id: value, ...}, ...}``.
    title
        Plot title.
    ax
        Optional matplotlib axes.

    Returns
    -------
    matplotlib.axes.Axes
        The axes used.

    Examples
    --------
    >>> data = {
    ...     "adobe":          {"IOD": 45.0, "dT_dt_max": 0.6},
    ...     "lightweight":    {"IOD": 92.0, "dT_dt_max": 2.4},
    ... }
    >>> # Used in the tutorial notebook to compare 4 typologies side by side.
    """
    plt = _require_matplotlib()
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    cases = list(kpi_results.keys())
    kpis_seen: list[str] = []
    for v in kpi_results.values():
        for k in v.keys():
            if k not in kpis_seen:
                kpis_seen.append(k)

    n_cases = len(cases)
    n_kpis = len(kpis_seen)
    if n_cases == 0 or n_kpis == 0:
        raise ValueError("kpi_results is empty.")

    bar_width = 0.8 / n_cases
    x = np.arange(n_kpis)
    palette = ["#1f4e79", "#2d6a2d", "#b8860b", "#7f5c00", "#595959"]

    for i, case in enumerate(cases):
        values = [kpi_results[case].get(k, np.nan) for k in kpis_seen]
        offset = (i - (n_cases - 1) / 2.0) * bar_width
        ax.bar(x + offset, values, width=bar_width,
               color=palette[i % len(palette)], label=case)

    ax.set_xticks(x)
    ax.set_xticklabels(kpis_seen, rotation=30, ha="right")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(loc="upper left", fontsize=9)
    return ax
