:orphan: true

BIG-IP Multi-Tenancy
====================

Overview
--------

One of BIG-IP®'s key features is the ability to virtualize the traffic management environment into customizable partitions. Typically referred to as multi-tenancy, this model allows admins to consolidate multiple services onto one BIG-IP. Using a multi-tenant, partitioned configuration allows admins to enable features on individual partitions based on each tenant's needs.

.. seealso::

    `Deploying Hosted and Cloud Services with BIG-IP Devices <https://www.f5.com/it-management/solution-profiles/hosted-cloud-services/>`_


.. todo:: include multi-tenancy diagram


Using BIG-IP VE to Provide LBaaS Services
-----------------------------------------

If you're using BIG-IP virtual edition(s) with the standard `Linux bridge <http://docs.openstack.org/liberty/networking-guide/scenario-provider-ovs.html>`_ or `Open vSwitch <http://docs.openstack.org/liberty/networking-guide/scenario-provider-lb.html>`_ Neutron core plugins, you can deploy LBaaS services in either of the following ways:

- :ref:`Global Routed Mode`: In Global Routed Mode, the BIG-IP VE is only connected to :ref:`provider networks <docs:provider-networks-bigip>`. All pool member L3 addresses must be routable using the Neutron router.

- :ref:`GRE, VLAN, or VxLAN tunnels <l2-l3-segmentation-modes>`: When using L2/L3 segmentation mode with GRE and/or VxLAN, you must connect the BIG-IP to your OpenStack  :ref:`provider network <docs:provider-networks-bigip>`. The provider network routes IP packets to the compute/network nodes' VTEP addresses through the Neutron router.

.. ifconfig:: openstack.release = Mitaka

    As of the Mitaka release the Linux bridge and Open vSwitch core plugins do not support the use of VLANs for tenant networks with multi-tenant Nova guest instances.

