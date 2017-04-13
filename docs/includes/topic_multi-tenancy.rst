:orphan: true

Manage Multi-Tenant BIG-IP Devices with F5 LBaaSv2
==================================================

Overview
--------

BIG-IP devices allow users to create and customize partitions for which specific features that meet a tenant's needs can be enabled. This type of configuration, called multi-tenancy, allows a greater degree of flexibility in allocating network resources to multiple individual projects. [#]_

    .. figure:: ../media/f5-lbaas-multi-tenancy.png
        :alt: Multi-tenant BIG-IP and F5 LBaaS
        :width: 500

        Multi-tenant BIG-IP and F5 LBaaS


Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` installed on the Neutron controller and all other hosts from which you want to provision LBaaS services.

- Knowledge of `OpenStack Networking <http://docs.openstack.org/liberty/networking-guide/>`_ concepts.

- Knowledge of BIG-IP `system configuration`_, `local traffic management`_, & `device service clustering`_.


Caveats
-------

When using BIG-IP Virtual Edition (VE) with the Linux bridge or Open vSwitch Neutron core plugins, F5 LBaaS can be deployed in two ways:

1) :ref:`Global Routed Mode`: BIG-IP VE is connected only to provider networks; all pool member L3 addresses must be routable using cloud infrastructure routers.

2) :ref:`L2 Segmentation Modes <L2 Segmentation Mode>` using GRE or VxLAN tunnels: BIG-IP VE has a data connection to a provider network which can route IP packets to the ``local_ip`` VTEP addresses of the compute and network nodes through a cloud infrastructure router.

.. As of the Mitaka release the Linux bridge and Open vSwitch core plugins do not support the use of VLANs for tenant networks with multi-tenant Nova guest instances.

Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo vi /etc/neutron/services/f5/f5-openstack-agent.ini

2. Configure the :ref:`L2 Segmentation Mode` settings as appropriate for your environment.

    * :ref:`Device VLAN to interface and tag mapping`

    * :ref:`VLAN device and interface to port mappings`

    * :ref:`Device Tunneling (VTEP) selfips` (if using VxLAN or GRE tunnels)

    * :ref:`Tunnel Types`

    * :ref:`Static ARP population for members on tunnel networks`


.. important::

    You must configure these settings correctly to ensure your tenant networks connect to the right interfaces on the BIG-IP(s) and that traffic is allowed to flow through the corresponding ports.


.. Further Reading
    ---------------
    .. seealso::
        * x
        * y
        * z

.. rubric:: Footnotes
.. [#] In OpenStack, the terms 'tenant' and 'project' are used interchangeably.


.. _system configuration: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid
.. _local traffic management: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html
.. _device service clustering: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html