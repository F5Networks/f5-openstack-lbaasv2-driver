Before You Begin
================

In order to use F5® LBaaSv2 services, you will need the following:

- Operational OpenStack cloud (|openstack| release).

- Licensed, operational BIG-IP® :term:`device` or :term:`device cluster`; can be deployed either as an OpenStack instance (BIG-IP VE) or external to the cloud (VE or hardware).

.. important::

    You must have the appropriate `license`_ for the BIG-IP features you wish to use.

    **The use of GRE or VxLAN tunnels requires an active BIG-IP SDN Services License.**

- Basic understanding of `OpenStack networking concepts`_.

- Basic understanding of `BIG-IP Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

- F5 :ref:`service provider package <Install the F5 Service Provider Package>` installed on the Neutron controller.

.. include:: includes/topic_tip-sudo-pip-git.rst
    :start-line: 2


Install the F5 Service Provider Package
---------------------------------------

.. warning:: If the F5 service provider package isn't installed on your Neutron controller, F5 LBaaSv2 will not work.

.. rubric:: Download the F5 LBaaSv2 service provider package and add it to the python path for ``neutron_lbaas``.

1. Download from GitHub.

.. code-block:: shell

    $ curl -O -L https://github.com/F5Networks/neutron-lbaas/releases/download/v8.0.1/f5.tgz


2. Install the service provider package on the Neutron controller.

    a. CentOS:

    .. code-block:: text

        $ sudo tar xvf f5.tgz -C /usr/lib/python2.7/site-packages/neutron_lbaas/drivers/

    b. Ubuntu:

    .. code-block:: text

        $ sudo tar xvf f5.tgz –C /usr/lib/python2.7/dist-packages/neutron_lbaas/drivers/


Install the F5 Agent
--------------------

.. topic:: To install the ``f5-openstack-agent`` package for v |release|:

    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-agent@v8.3.0.b2

    .. tip::

        See the :ref:`F5 Agent documentation <agent:home>` for rpm and dpkg installation instructions.


Install the F5 LBaaSv2 Driver
-----------------------------

.. include:: includes/topic_install-f5-lbaasv2-driver.rst
    :start-line: 5


.. seealso:: :ref:`Basic Environment Requirements for F5 LBaaSv2`


.. _license: https://f5.com/products/how-to-buy/simplified-licensing
.. _OpenStack Networking Concepts: http://docs.openstack.org/liberty/networking-guide/
