aridkpi documentation
=====================

**Climate-resilience KPIs for residential buildings in arid South American climates.**

``aridkpi`` is a Python package implementing the 5 core indicators of the
`KPI Comparison Matrix v1.0 <https://doi.org/10.5281/zenodo.19964373>`_,
aligned with the `IEA EBC Annex 80 <https://annex80.iea-ebc.org/>`_ framework
and extended for arid and semi-arid climates of South America (BWk/BSk
Köppen-Geiger).

.. note::

   Designed at INAHE-CONICET Mendoza for the 2026–2029 research plan
   *Towards an integrated climate metric for building performance*.

Quick links
-----------

- :doc:`installation`
- :doc:`tutorial`
- :doc:`api/index`
- `KPI Comparison Matrix v1.0 <https://doi.org/10.5281/zenodo.19964373>`_
- `Source code on GitHub <https://github.com/gbarea-INAHE/aridkpi>`_

What it computes
----------------

.. list-table::
   :header-rows: 1
   :widths: 20 60 20

   * - KPI
     - Description
     - Units
   * - ``iod``
     - Indoor Overheating Degree — magnitude of overheating during occupied hours
     - °C·h
   * - ``ccor``
     - Climate Change Overheating Resistivity — effectiveness of a passive strategy
     - °C·h/°C
   * - ``udh``
     - Unmet Degree Hours during outage (Passive Survivability)
     - °C·h
   * - ``energy_climate_sensitivity``
     - ΔE/ΔT — slope of EUI vs T_mean across SSP scenarios
     - kWh·m⁻²·yr⁻¹/°C
   * - ``max_thermal_change_rate``
     - dT/dt max — peak indoor thermal change rate
     - °C/h

Quick start
-----------

.. code-block:: python

   import aridkpi

   df = aridkpi.synth.synthetic_dataset(typology="masonry_insulated", days=14, seed=42)
   overheating = aridkpi.iod(df["T_in"], T_comf=26.0)
   peak_rate = aridkpi.max_thermal_change_rate(df["T_in"])

   print(f"IOD = {overheating:.1f} deg-C-h")
   print(f"dT/dt max = {peak_rate:.2f} deg-C/h")

Citation
--------

Please cite both the package and the underlying KPI matrix:

.. code-block:: bibtex

   @software{barea_aridkpi_2026,
     author    = {Barea Paci, Gustavo Javier},
     title     = {aridkpi: climate-resilience KPIs for residential buildings},
     year      = {2026},
     version   = {0.1.0},
     publisher = {Zenodo},
     doi       = {10.5281/zenodo.19986567}
   }

Table of contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   installation
   tutorial

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/index

.. toctree::
   :maxdepth: 1
   :caption: About

   changelog
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
