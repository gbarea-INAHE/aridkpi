Tutorial
========

A complete walkthrough is available as a Jupyter notebook in the
repository: `notebooks/tutorial.ipynb
<https://github.com/gbarea-INAHE/aridkpi/blob/main/notebooks/tutorial.ipynb>`_.

Below is the same tutorial transcribed for reading inline.

1. Generate synthetic data
--------------------------

.. code-block:: python

   import aridkpi

   df = aridkpi.synth.synthetic_dataset(
       start="2026-01-15",
       days=14,
       typology="masonry_insulated",
       seed=42,
   )

The ``typology`` argument selects one of four prototype envelopes:

* ``"adobe"`` — high mass, low attenuation, large phase lag
* ``"masonry_no_insulation"`` — medium mass
* ``"masonry_insulated"`` — current Argentine standard (IRAM 11605)
* ``"lightweight"`` — industrialised, low mass

2. Compute the 5 CORE KPIs
--------------------------

Indoor Overheating Degree (IOD)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   iod_value = aridkpi.iod(df["T_in"], T_comf=26.0)

Maximum thermal change rate (dT/dt max)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   peak_rate = aridkpi.max_thermal_change_rate(df["T_in"])

UDH during a 72-hour outage
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   outage_start = df["T_ext"].idxmax().normalize()
   udh_value = aridkpi.udh(
       df["T_in"],
       outage_start=outage_start,
       window="72h",
       threshold=30.0,
   )

CCOR (climate change overheating resistivity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   df_baseline = aridkpi.synth.synthetic_dataset(
       typology="lightweight", days=14, seed=42,
   )
   iod_baseline = aridkpi.iod(df_baseline["T_in"], T_comf=26.0)
   iod_strategy = aridkpi.iod(df["T_in"], T_comf=26.0)
   ccor_value = aridkpi.ccor(iod_baseline, iod_strategy, delta_T_climate=2.5)

ΔE/ΔT
~~~~~

.. code-block:: python

   import pandas as pd

   ssp_results = pd.DataFrame({
       "T_mean": [16.5, 17.4, 18.2, 19.1, 21.0],
       "EUI":    [82.0, 86.5, 92.0, 98.0, 110.0],
   })
   sensitivity = aridkpi.energy_climate_sensitivity(ssp_results)
   slope = sensitivity["slope"]   # kWh / m^2 / yr / deg-C

3. Loading real data
--------------------

.. code-block:: python

   df_hobo = aridkpi.io.load_hobo_csv("logger_export.csv")
   df_eplus = aridkpi.io.load_energyplus_csv("eplusout.csv")
   df_csv = aridkpi.io.load_generic_csv("my_data.csv", timestamp_col="datetime")

   aridkpi.io.ensure_valid(df_hobo["T"], max_gap_minutes=15.0)

4. Visualisation
----------------

.. code-block:: python

   ax = aridkpi.viz.plot_temperature_series(df["T_in"], df["T_ext"])
   ax = aridkpi.viz.plot_overheating_diagnostic(df["T_in"], T_comf=26.0)
