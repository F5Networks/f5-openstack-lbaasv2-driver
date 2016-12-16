:orphan: true

Install the F5 LBaaSv2 Driver
-----------------------------

Quick Start
```````````

.. rubric:: Install the ``f5-openstack-lbaasv2-driver`` package for v |release|:

.. code-block:: text

    $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@v8.2.0.b1


.. tip::

    You can install packages from HEAD on a specific branches by adding ``@<branch_name>`` to the end of the install command instead of the release tag.

    .. rubric:: Example:
    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@liberty


.. warning::

    You must :ref:`install the f5-openstack-agent <agent:home>` package, and its dependencies, **before** installing the f5-openstack-lbaasv2-driver via ``dpkg`` or ``rpm``.


Debian Package
``````````````

The ``f5-openstack-lbaasv2-driver`` package can be installed using ``dpkg``.

1. Download the package:

.. code-block:: bash

    $ curl –L –O https://github.com/F5Networks/f5-openstack-lbaasv2-driver/releases/download/v8.2.0.b1/python-f5-openstack-lbaasv2-driver_8.2.0.b1-1_1404_all.deb

2. Install the package on the Neutron controller:

.. code-block:: bash

    $ sudo dpkg –i python-f5-openstack-lbaasv2-driver_8.2.0.b1-1_1404_all.deb

RPM Package
```````````

The ``f5-openstack-lbaasv2-driver`` package can be installed using ``rpm``.

1. Download the package:

.. code-block:: bash

    $ curl –L –O https://github.com/F5Networks/f5-openstack-lbaasv2-driver/releases/download/v8.2.0.b1/f5-openstack-lbaasv2-driver-8.2.0.b1-1.el7.noarch.rpm

2. Install the package on the Neutron controller:

.. code-block:: bash

    $ sudo rpm –ivh f5-openstack-lbaasv2-driver-8.2.0.b1-1.el7.noarch.rpm


