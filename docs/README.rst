F5 Driver for OpenStack LBaaSv2
===============================

.. sidebar:: **OpenStack version:**

    |openstack|

|Build Status|


.. raw:: html

    <script async defer src="https://f5-openstack-slack.herokuapp.com/slackin.js"></script>

.. toctree::
   :titlesonly:
   :hidden:

   environment-generator

version |release|
-----------------

|release-notes|

The |driver-long| is a Neutron LBaaSv2 service provider driver (``f5lbaasdriver``) that runs within the `OpenStack Neutron`_ controller.
The |driver-short| is an alternative to the default Neutron LBaaS service provider driver.
It enables use of F5 BIG-IP Local Traffic Manager services in an OpenStack cloud.

Architecture
------------

The |driver-long| runs within the OpenStack Neutron controller processes.
<<<<<<< HEAD
It watches the Neutron RPC messaging queue for calls to the `Neutron LBaaS API`_ and schedules tasks to the `F5 Agent for OpenStack Neutron`_.
=======
It watches the Neutron RPC messaging queue for calls to the `Neutron LBaaS API`_ and schedules tasks to the `F5 BIG-IP Controller for OpenStack`_.
>>>>>>> 5cbb070... Fixes #669
The |agent-long| uses iControl REST API calls to apply the desired configurations to BIG-IP device(s).

Guides
------

See the `F5 Driver for OpenStack LBaaSv2 user documentation`_.

.. index::
   triple: lbaasv2-driver; downloads; debian
   triple: lbaasv2-driver; downloads; rpm

Downloads
---------

|deb-download| |rpm-download|


.. index::
   single: lbaasv2-driver; install

Installation
------------

.. important::

<<<<<<< HEAD
   * You must download and install the `F5 Agent for OpenStack Neutron`_ and the :ref:`F5 Service Provider Package <f5-sp-package-install>` **before** you install the F5 LBaaSv2 driver.
=======
   * You must download and install the `F5 BIG-IP Controller for OpenStack`_ and the :ref:`F5 Service Provider Package <f5-sp-package-install>` **before** you install the F5 LBaaSv2 driver.
>>>>>>> 5cbb070... Fixes #669

   * Install the |driver-long| on your Neutron controller.

.. index::
   single: install; F5 service provider package

.. _f5-sp-package-install:

F5 Service Provider Package
```````````````````````````

The F5 service provider package preps your Neutron installation for use with the |driver-long|.
**This is a required package. The F5 OpenStack LBaaS Solution will not work if this package isn't installed.**

You'll need to download the F5 LBaaSv2 service provider package and add it to the python path for ``neutron_lbaas``, then download and install the |driver-short|.


.. _driver-install-deb:

.. index::
   triple: lbaasv2-driver; install; debian

Debian
``````

.. parsed-literal::

   curl -O -L |f5_lbaasv2_driver_shim_url|
   sudo tar xvf f5.tgz -C /usr/lib/python2.7/dist-packages/neutron_lbaas/drivers/
   curl –L –O |f5_lbaasv2_driver_deb_url|
   dpkg –i |f5_lbaasv2_driver_deb_package|



.. index::
   triple: lbaasv2-driver; install; pip

.. _driver-install-pip:

Pip
```

Download and install the F5 service provider package, then ``pip install`` the package from GitHub.

.. parsed-literal::

   pip install |f5_lbaasv2_driver_pip_url|

.. tip::

   Use ``@<branch-name>`` to install from HEAD on a specific branch. For example:

   .. parsed-literal::

      pip install |f5_lbaasv2_driver_pip_url_branch|

.. index::
   triple: lbaasv2-driver; install; rpm


.. _driver-install-rpm:

RPM
```

.. parsed-literal::

   curl -O -L |f5_lbaasv2_driver_shim_url|
   sudo tar xvf f5.tgz -C /usr/lib/python2.7/site-packages/neutron_lbaas/drivers/
   curl –L –O |f5_lbaasv2_driver_rpm_url|
   rpm –ivh |f5_lbaasv2_driver_rpm_package|


.. index::
   single: lbaasv2-driver; Neutron setup

.. _configure-neutron-lbaasv2-driver:

Neutron Setup
-------------

Take the steps below to tell Neutron to use the F5 service provider driver and the LBaaSv2 service plugin.

.. note::

   The config file names/locations may vary depending on your OpenStack platform.
   See `Partners`_ for a list of F5's certified OpenStack distribution partners and links to their documentation.


#. Add 'F5Networks' to the ``service_providers`` section of the Neutron LBaaS config file: :file:`/etc/neutron/neutron_lbaas.conf` as shown below.

   .. code-block:: text
      :emphasize-lines: 4

      $ vim /etc/neutron/neutron_lbaas.conf
      ...
      [service_providers]
      service_provider = LOADBALANCERV2:F5Networks:neutron_lbaas.drivers.f5.driver_v2.F5LBaaSV2Driver:default
      ...

#. Add the LBaaSv2 service plugin to the ``[DEFAULT]`` section of the Neutron config file: :file:`/etc/neutron/neutron.conf`.

   .. code-block:: text

      $ vi /etc/neutron/neutron.conf
      ...
      [DEFAULT]
      service_plugins = [already defined plugins],neutron_lbaas.services.loadbalancer.plugin.LoadBalancerPluginv2
      ...

   .. note::

      If you have previously used the LBaaSv1 service plugin (``lbaas``), remove it.
      The two cannot run simultaneously.


#. Restart Neutron

   .. code-block:: text

      $ sudo service neutron-server restart    \\ Ubuntu
      $ sudo systemctl restart neutron-server  \\ CentOS


What's Next
-----------

`Configure and start`_ the |agent-long|.

.. seealso::

   `F5 Driver for OpenStack LBaaSv2 user documentation`_


.. |Build Status| image:: https://travis-ci.org/F5Networks/f5-openstack-lbaasv2-driver.svg?branch=liberty
    :target: https://travis-ci.org/F5Networks/f5-openstack-lbaasv2-driver
    :alt: Build Status


.. _OpenStack Neutron: https://docs.openstack.org/developer/neutron/
.. _F5 Agent for OpenStack Neutron: /products/openstack/latest/agent/
.. _F5 Driver for OpenStack LBaaSv2 user documentation: /cloud/openstack/latest/lbaas
.. _Neutron LBaaS API: https://wiki.openstack.org/wiki/Neutron/LBaaS/API_2.0
.. _available F5 agent: /products/openstack/latest/agent/
.. _F5 Service Provider Package: /cloud/openstack/latest/lbaas-prep
.. _Download the latest debian package: |f5_lbaasv2_driver_deb_url|
.. _Download the latest rpm package: |f5_lbaasv2_driver_rpm_url|
.. _Partners: /cloud/openstack/latest/support/partners.html
.. _Configure and start: /products/openstack/latest/agent/index.html#configure-the-agent-long
