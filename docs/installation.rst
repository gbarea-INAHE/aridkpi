Installation
============

Requirements
------------

* Python 3.10 or newer
* numpy >= 1.24
* pandas >= 2.0
* scipy >= 1.10

From PyPI
---------

.. code-block:: bash

   pip install aridkpi

With visualisation support
--------------------------

.. code-block:: bash

   pip install aridkpi[viz]

The visualisation extras add ``matplotlib >= 3.7``.

With EnergyPlus loader
----------------------

.. code-block:: bash

   pip install aridkpi[energyplus]

The EnergyPlus extras add ``eppy``.

Everything (development install)
--------------------------------

.. code-block:: bash

   pip install aridkpi[all]

For development from source:

.. code-block:: bash

   git clone https://github.com/gbarea-INAHE/aridkpi.git
   cd aridkpi
   pip install -e .[dev]
