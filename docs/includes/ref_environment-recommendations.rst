Environment Recommendations
===========================

There are many, many different ways to configure OpenStack and many different operating systems from which to choose. Here are some basic recommendations and requirements that make up what we consider to be a 'functional OpenStack environment'.

Deploying OpenStack
-------------------

We use a development environment :ref:`deployed with Packstack <docs:OpenStack Deployment Guide>` for most of our documentation and testing. You may also consider using `DevStack <http://docs.openstack.org/developer/devstack/>`_, or opting to go with a solution from one of F5 Networks' certified `partners <https://f5.com/solutions/technology-alliances/openstack>`_.

Regardless of how you choose to deploy OpenStack, we recommend that you include the following core & optional services. Each of these is necessary for one or more F5® OpenStack integrations.

- `Nova`_ - compute
- `Neutron`_ - networking
- `Keystone`_ - identity
- `Glance`_ - image service
- `Horizon`_ - dashboard
- `Heat`_ - orchestration
- `Barbican`_ - key management


Configuring OpenStack
---------------------

The basics of configuring OpenStack are covered in our :ref:`config guide <docs:OpenStack Configuration Guide>`. We suggest you keep the following details in mind when configuring your environment.

Minimum Requirements
~~~~~~~~~~~~~~~~~~~~

.. list-table::



OpenStack:
 - One (1) controller, one (1) compute, and one (1) networking node; *can be an all-in-one deployment*.
 - One :ref:`provider network <docs:Neutron - Provider Networks>`.
 - One (1) VLAN

BIG-IP:
- A licensed, operational BIG-IP device that meets the OpenStack :ref:`compatibility requirements <docs:releases-and-support>`.
    - :term:`one-arm mode`: one (1) nic and one (1) VLAN
    - :term:`multi-arm mode`: at least two (2) nics and two (2) VLANS




.. todo:: add network topology descriptions and diagrams (from lbaasv1) to this doc set


Basic Recommendations
~~~~~~~~~~~~~~~~~~~~~

- :term:`Overcloud`: One (1) BIG-IP device with two (2) nics, two (2) VLANS (management & data)
- :term:`Undercloud`: One (1) BIG-IP device with two (2) nicstwo (2) VLANS; must have a VXLAN or GRE VTEP
- :term:`Clustering`: Two (2) BIG-IP devices with three (3) nics each; management, data, and :term:`high availability` (HA).




.. _Nova: http://www.openstack.org/software/releases/liberty/components/nova
.. _Neutron: http://www.openstack.org/software/releases/liberty/components/neutron
.. _Keystone: http://www.openstack.org/software/releases/liberty/components/keystone
.. _Glance: http://www.openstack.org/software/releases/liberty/components/glance
.. _Horizon: http://www.openstack.org/software/releases/liberty/components/horizon
.. _Heat: http://www.openstack.org/software/releases/liberty/components/heat
.. _Barbican: http://www.openstack.org/software/releases/liberty/components/barbican
