# aridkpi

[![Tests](https://github.com/gbarea-INAHE/aridkpi/actions/workflows/tests.yml/badge.svg)](https://github.com/gbarea-INAHE/aridkpi/actions/workflows/tests.yml)
[![Documentation](https://github.com/gbarea-INAHE/aridkpi/actions/workflows/docs.yml/badge.svg)](https://gbarea-INAHE.github.io/aridkpi/)
[![PyPI version](https://img.shields.io/pypi/v/aridkpi.svg)](https://pypi.org/project/aridkpi/)
[![Python](https://img.shields.io/pypi/pyversions/aridkpi.svg)](https://pypi.org/project/aridkpi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.YYYYYYY.svg)](https://doi.org/10.5281/zenodo.YYYYYYY)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Climate-resilience KPIs for residential buildings in arid South American climates.**

`aridkpi` is a Python package implementing the 5 core indicators of the
[KPI Comparison Matrix v1.0](https://doi.org/10.5281/zenodo.19964373),
aligned with the [IEA EBC Annex 80](https://annex80.iea-ebc.org/) framework
and extended for arid and semi-arid climates of South America (BWk/BSk
Köppen-Geiger).

> Designed at INAHE-CONICET Mendoza for the 2026–2029 research plan
> *"Towards an integrated climate metric for building performance"*.

---

## What it computes

| KPI | Description | Units |
|---|---|---|
| `iod` | **Indoor Overheating Degree** — magnitude of overheating during occupied hours | °C·h |
| `ccor` | **Climate Change Overheating Resistivity** — effectiveness of a passive strategy | °C·h/°C |
| `udh` | **Unmet Degree Hours during outage** (Passive Survivability) — habitability without power | °C·h |
| `energy_climate_sensitivity` | **ΔE/ΔT** — slope of EUI vs T_mean across SSP scenarios | kWh·m⁻²·yr⁻¹/°C |
| `max_thermal_change_rate` | **dT/dt max** — peak indoor thermal change rate | °C/h |

For each KPI: formal definition, assumptions, limitations in BWk/BSk and
rationale for regional extension are documented in the
[KPI Comparison Matrix v1.0](https://doi.org/10.5281/zenodo.19964373).

---

## Installation

```bash
pip install aridkpi
```

With visualisation support:

```bash
pip install aridkpi[viz]
```

With EnergyPlus loader:

```bash
pip install aridkpi[energyplus]
```

Everything (recommended for development):

```bash
pip install aridkpi[all]
```

---

## Quick start

```python
import aridkpi

# 1. Generate synthetic data for a typical Mendoza house (2 weeks, January)
df = aridkpi.synth.synthetic_dataset(
    start="2026-01-15",
    days=14,
    typology="masonry_insulated",
    seed=42,
)

# 2. Compute the 5 CORE KPIs
overheating   = aridkpi.iod(df["T_in"], T_comf=26.0)
peak_rate     = aridkpi.max_thermal_change_rate(df["T_in"])
survivability = aridkpi.udh(
    df["T_in"],
    outage_start=df["T_ext"].idxmax().normalize(),
    window="72h",
    threshold=30.0,
)

print(f"IOD = {overheating:.1f} deg-C-h")
print(f"dT/dt max = {peak_rate:.2f} deg-C/h")
print(f"UDH 72h = {survivability:.1f} deg-C-h")
```

For a complete walkthrough see the
[tutorial notebook](notebooks/tutorial.ipynb).

---

## Loading real data

```python
df = aridkpi.io.load_hobo_csv("logger_export.csv")
df = aridkpi.io.load_energyplus_csv("eplusout.csv")
df = aridkpi.io.load_generic_csv("my_data.csv", timestamp_col="datetime")

aridkpi.io.ensure_valid(df["T_in"], max_gap_minutes=15.0)
```

---

## Comparing typologies

```python
typologies = ["adobe", "masonry_no_insulation",
              "masonry_insulated", "lightweight"]
results = {}
for t in typologies:
    d = aridkpi.synth.synthetic_dataset(typology=t, days=14, seed=42)
    results[t] = {
        "IOD":       aridkpi.iod(d["T_in"], T_comf=26.0),
        "dT/dt_max": aridkpi.max_thermal_change_rate(d["T_in"]),
    }

import aridkpi.viz as viz
viz.plot_kpi_summary(results, title="Typology comparison")
```

---

## Why an arid-climate-specific package?

The Annex 80 framework was calibrated on European temperate climates and
North American humid heat waves. South American arid climates (BWk/BSk)
present three departures that break key assumptions:

* Diurnal range > 15 deg-C (vs ~8 in temperate Europe).
* Mean RH < 40 percent during summer (vs > 60 in humid heat waves).
* Solar radiation > 2200 kWh per m2 per year (vs ~1200 in central Europe).

The KPI Comparison Matrix documents these departures and the rationale for
regional extensions; `aridkpi` implements the indicators with sensible
defaults for the regional context and provides hooks (e.g. supplying an
adaptive `T_comf` series) to replace those defaults with locally validated
values.

---

## How to cite

```bibtex
@software{barea_aridkpi_2026,
  author    = {Barea Paci, Gustavo Javier},
  title     = {aridkpi: climate-resilience KPIs for residential buildings
               in arid South American climates},
  year      = {2026},
  version   = {0.1.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.YYYYYYY},
  url       = {https://github.com/gbarea-INAHE/aridkpi}
}
```

Please cite both the package **and** the underlying
[KPI Comparison Matrix v1.0](https://doi.org/10.5281/zenodo.19964373).

---

## Documentation

Full documentation: <https://gbarea-INAHE.github.io/aridkpi/>

Local build:

```bash
pip install aridkpi[dev]
cd docs && make html
```

---

## Development

```bash
git clone https://github.com/gbarea-INAHE/aridkpi.git
cd aridkpi
pip install -e .[dev]
pytest                    # run tests
ruff check .              # lint
mypy src/aridkpi          # type check
```

Tests run on Python 3.10, 3.11 and 3.12 (Linux, macOS, Windows) via
GitHub Actions.

---

## Acknowledgements

Developed at the **Instituto de Ambiente, Hábitat y Energía (INAHE)**, CONICET
Mendoza. The framework articulates collaboration with C. Filippín
(CONICET — La Pampa), S. Flores Larsen (CONICET — Salta), F. Bre and
V. Fachinotti (CIMEC — Santa Fe), C. Ganem and M. V. Mercado
(INAHE — Mendoza), and A. Esteves (INAHE — Mendoza).

This software is the second deliverable of the 2026–2029 research plan
*"Hacia una métrica climática integrada del desempeño edilicio"* presented to
the Carrera del Investigador Científico of CONICET.

---

## License

[MIT](LICENSE) (c) 2026 Gustavo Javier Barea Paci
