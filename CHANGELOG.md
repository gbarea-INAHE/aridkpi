# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-05-02

Initial public release. Implements the 5 CORE KPIs of the
[KPI Comparison Matrix v1.0](https://doi.org/10.5281/zenodo.19964373).

**DOI:** [10.5281/zenodo.19986567](https://doi.org/10.5281/zenodo.19986567)

### Added

- **Core KPIs (`aridkpi.core`)**:
  - `iod()`        — Indoor Overheating Degree
  - `ccor()`       — Climate Change Overheating Resistivity
  - `udh()`        — Unmet Degree Hours during outage (Passive Survivability)
  - `energy_climate_sensitivity()` — ΔE/ΔT linear regression
  - `max_thermal_change_rate()`    — dT/dt max
- **Data loaders (`aridkpi.io`)**:
  - `load_hobo_csv()`        — Onset HOBO MX-series CSV
  - `load_generic_csv()`     — generic CSV with timestamp + numeric columns
  - `load_energyplus_csv()`  — EnergyPlus eplusout.csv (T_op and T_air)
  - `ensure_valid()`         — pre-computation sanity check
- **Synthetic data (`aridkpi.synth`)**:
  - `synthetic_outdoor_temperature()`
  - `synthetic_indoor_temperature()` parametrised by attenuation and phase lag
  - `synthetic_relative_humidity()`
  - `synthetic_dataset()` for 4 prototype envelopes (adobe, masonry without
    insulation, masonry with insulation IRAM 11605, lightweight)
- **Visualisation (`aridkpi.viz`)** — optional, requires matplotlib:
  - `plot_temperature_series()` — indoor + outdoor + comfort threshold
  - `plot_overheating_diagnostic()` — visual interpretation of IOD
  - `plot_kpi_summary()` — bar chart comparing typologies
- **Tests**: 57 tests covering all public API, 88% coverage.
- **Docs**: Sphinx site at https://gbarea-inahe.github.io/aridkpi/ + tutorial notebook.
- **CI/CD**: GitHub Actions for tests (Linux/macOS/Windows × Python 3.10/3.11/3.12),
  documentation deployment, and PyPI publishing.

### Implementation notes

- All KPIs follow exactly the formal definitions in the KPI Comparison Matrix v1.0.
- Defaults align with the IEA EBC Annex 80 conventions but are documented as
  regional-extension hooks (e.g. `T_comf=26.0` is the default but the user can
  supply a Series for adaptive comfort models).
- All temperature series require a `pandas.DatetimeIndex` and are validated
  before computation.
- The package is typed (Python 3.10+ type hints) and passes `mypy`.

### External resources

- Indexed in OpenAIRE
- Archived in Software Heritage
- Companion software to the
  [KPI Comparison Matrix v1.0](https://doi.org/10.5281/zenodo.19964373)
