:orphan: true

BIG-IP Multi-Tenancy
====================

Overview
--------

One of BIG-IP®'s key features is the ability to virtualize the traffic management environment into customizable partitions. Typically referred to as multi-tenancy, this model allows admins to consolidate multiple services onto one BIG-IP. Using a multi-tenant, partitioned configuration allows admins to enable features on individual partitions based on each tenant's needs.

.. seealso::

    `Deploying Hosted and Cloud Services with BIG-IP Devices <https://www.f5.com/it-management/solution-profiles/hosted-cloud-services/>`_


.. todo:: include multi-tenancy diagram


Use Case
--------

Prerequisites
-------------

Caveats
-------

- :ref:`Global routed mode` is not compatible with multi-tenancy.

- When using :ref:`L2/L3 segmentation mode <l2-l3-segmentation-modes>` with GRE, VLAN, and/or VxLAN tunnels, you must connect the BIG-IP device(s) to your OpenStack :ref:`provider network <docs:provider-networks-bigip>` via the Neutron router.

.. As of the Mitaka release the Linux bridge and Open vSwitch core plugins do not support the use of VLANs for tenant networks with multi-tenant Nova guest instances.

Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini

2. Configure the :ref:`L2 segmentation mode` settings as appropriate for your environment.

    Specifically, you will need to configure the Device VLAN to interface and tag mapping and/or VLAN device and interface to port mappings to ensure your tenant networks connect to the correct interfaces on your BIG-IP, and that traffic is allowed to flow through the corresponding ports.


Further Reading
---------------

.. seealso::

    * x
    * y
    * z
