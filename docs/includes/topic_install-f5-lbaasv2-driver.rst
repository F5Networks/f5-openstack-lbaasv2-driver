:orphan: true

Install the F5 LBaaSv2 Driver
-----------------------------

Quick Start
```````````

.. rubric:: Install the ``f5-openstack-lbaasv2-driver`` package for v |release|:

.. code-block:: text

    $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@v9.0.3

.. tip::

    You can install packages from HEAD on a specific branches by adding ``@<branch_name>`` to the end of the install command instead of the release tag.

    .. rubric:: Example:
    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@mitaka


.. warning::

    You must :ref:`install the f5-openstack-agent <agent:home>` package, and its dependencies, **before** installing the f5-openstack-lbaasv2-driver via ``dpkg`` or ``rpm``.


Debian Package
``````````````

The ``f5-openstack-lbaasv2-driver`` package can be installed using ``dpkg``.

1. Download the package:

.. code-block:: bash

    $ curl –L –O https://github.com/F5Networks/f5-common-python/releases/download/v9.0.3/python-f5-openstack-agent_9.0.3-1_1404_all.deb

2. Install the package on the Neutron controller:

.. code-block:: bash

    $ sudo dpkg –i python-f5-openstack-driver_9.0.3-1_1404_all.deb

RPM Package
```````````

The ``f5-openstack-lbaasv2-driver`` package can be installed using ``rpm``.

1. Download the package:

.. code-block:: bash

    $ curl –L –O https://github.com/F5Networks/f5-openstack-lbaasv2-driver/releases/download/v9.0.3/f5-openstack-lbaasv2-driver-9.0.3-1.el7.noarch.rpm

2. Install the package on the Neutron controller:

.. code-block:: bash

    $ sudo rpm –ivh f5-openstack-lbaasv2-driver-9.0.3-1.el7.noarch.rpm

.. tip:: Release tags always use the format "vx.x.x"
