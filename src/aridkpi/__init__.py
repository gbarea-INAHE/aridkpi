"""
aridkpi — climate-resilience KPIs for residential buildings in arid
South American climates (BWk/BSk).

This package implements the 5 CORE indicators of the KPI Comparison Matrix
v1.0 (Barea Paci, 2026), aligned with the IEA EBC Annex 80 framework and
extended for the regional context.

Quick start
-----------

>>> import aridkpi
>>> df = aridkpi.synth.synthetic_dataset(typology="masonry_insulated", days=14)
>>> overheating = aridkpi.iod(df["T_in"], T_comf=26.0)
>>> peak_rate = aridkpi.max_thermal_change_rate(df["T_in"])

Modules
-------

* ``aridkpi.core``  — the 5 CORE KPIs.
* ``aridkpi.io``    — data loaders (HOBO CSV, EnergyPlus, generic).
* ``aridkpi.synth`` — synthetic-data generators for testing and tutorials.
* ``aridkpi.viz``   — matplotlib visualisation utilities (optional dependency).

Citation
--------

Please cite both the package and the underlying KPI matrix:

* Software:
    Barea Paci, G. J. (2026). aridkpi v0.1.0 (Software).
    Zenodo. https://doi.org/10.5281/zenodo.19986567

* Underlying matrix:
    Barea Paci, G. J. (2026). KPI Comparison Matrix v1.0 (Dataset).
    Zenodo. https://doi.org/10.5281/zenodo.19964373
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import core, io, synth
from .core import (
    ccor,
    energy_climate_sensitivity,
    iod,
    max_thermal_change_rate,
    udh,
)

# viz is imported lazily because matplotlib is an optional dependency
try:
    from . import viz  # noqa: F401
    _has_viz = True
except ImportError:  # pragma: no cover
    _has_viz = False

__all__ = [
    "__version__",
    "ccor",
    # Modules
    "core",
    "energy_climate_sensitivity",
    "io",
    # Core KPIs (re-exported from .core for convenience)
    "iod",
    "max_thermal_change_rate",
    "synth",
    "udh",
]

if _has_viz:
    __all__.append("viz")
