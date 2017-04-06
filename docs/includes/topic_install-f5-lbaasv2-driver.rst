:orphan: true

Install the F5 LBaaSv2 Driver
-----------------------------

Quick Start
```````````

.. rubric:: Install the ``f5-openstack-lbaasv2-driver`` package for v |release|:

.. parsed-literal::

    $ sudo pip install |f5_lbaasv2_driver_pip_url|


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

.. parsed-literal::

    $ curl –L –O |f5_lbaasv2_driver_deb_url|

2. Install the package on the Neutron controller:

.. parsed-literal::

    $ sudo dpkg –i |f5_lbaasv2_driver_deb_package|

RPM Package
```````````

The ``f5-openstack-lbaasv2-driver`` package can be installed using ``rpm``.

1. Download the package:

.. parsed-literal::

    $ curl –L –O |f5_lbaasv2_driver_rpm_url|

2. Install the package on the Neutron controller:

.. parsed-literal::

    $ sudo rpm –ivh |f5_lbaasv2_driver_rpm_package|


