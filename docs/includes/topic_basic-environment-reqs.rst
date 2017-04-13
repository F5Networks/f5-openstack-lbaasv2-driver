:orphan: true
:hidden:

Basic Environment Requirements for F5 LBaaSv2
=============================================

This document provides the minimum basic requirements for using F5 LBaaSv2 in OpenStack |openstack|.

OpenStack Requirements
----------------------

The OpenStack installation guides cover the requirements for specific environments.

    - `Installation Guide for Red Hat Enterprise Linux 7 and CentOS 7`_
    - `Installation Guide for Ubuntu 14.04 (LTS)`_
    - `OpenStack Installation Guide for openSUSE and SUSE Linux Enterprise`_

We recommend that you install and configure the following OpenStack services. Each of these is necessary for one or more F5 OpenStack integrations.

+-------------+-------------------------+-----------------------+
| Service     | Description             | F5 Integration        |
+=============+=========================+=======================+
| `Nova`_     | compute service         | LBaaSv2, Heat         |
+-------------+-------------------------+-----------------------+
| `Neutron`_  | networking              | LBaaSv2               |
+-------------+-------------------------+-----------------------+
| `Keystone`_ | identity                | LBaaSv2, Heat         |
+-------------+-------------------------+-----------------------+
| `Glance`_   | image service           | Heat                  |
+-------------+-------------------------+-----------------------+
| `Horizon`_  | dashboard               | LBaaSv2 [#]_, Heat    |
+-------------+-------------------------+-----------------------+
| `Heat`_     | orchestration           | Heat                  |
+-------------+-------------------------+-----------------------+
| `Barbican`_ | key management          | LBaaSv2               |
+-------------+-------------------------+-----------------------+


BIG-IP Requirements
-------------------

.. important::

    - You must have the appropriate `license`_ for the BIG-IP features you wish to use.

    - All numbers shown in the table below are per BIG-IP device.


.. table:: BIG-IP Requirements

    +----------------------------+--------+------------+----------------+-------------+-----------------+
    | Deployment [#]_            | NICs   | VLANs [#]_ | Tunnels [#]_   | VTEPs [#]_  | License         |
    +============================+========+============+================+=============+=================+
    | Standalone overcloud       | 2      | 2          | n/a            | n/a         | any             |
    +----------------------------+--------+------------+----------------+-------------+-----------------+
    | Standalone undercloud      | 2      | 2          | 1              | 1           | better or best  |
    +----------------------------+--------+------------+----------------+-------------+-----------------+
    | Pair overcloud             | 3      | 3          | n/a            | n/a         | any             |
    +----------------------------+--------+------------+----------------+-------------+-----------------+
    | Pair undercloud            | 3      | 3          | 1              | 1           | better or best  |
    +----------------------------+--------+------------+----------------+-------------+-----------------+
    | Scalen cluster overcloud   | 3      | 3          | n/a            | n/a         | any             |
    +----------------------------+--------+------------+----------------+-------------+-----------------+
    | Scalen cluster undercloud  | 3      | 3          | 1              | 1           | better or best  |
    +----------------------------+--------+------------+----------------+-------------+-----------------+


.. seealso::

    - :ref:`F5 OpenStack Releases and Support Matrix <docs:F5 OpenStack Releases and Support Matrix>`

    - `BIG-IP LTM Release Notes`_


.. rubric:: Footnotes

.. [#] The `LBaaSv2 dashboard panels`_ are available in OpenStack Mitaka and later releases.
.. [#] Click on a term to view its definition: :term:`overcloud`; :term:`undercloud`; :term:`standalone`; :term:`pair`; :term:`scalen`; :term:`cluster`
.. [#] Two VLANS = data & management. Three VLANS = data, management, and HA. See `Configuring the basic BIG-IP network`_ for more information.
.. [#] Tunnels can be either VxLAN or GRE.
.. [#] If you're using a tunnel to reach an undercloud BIG-IP, you must configure the VTEP at which it can be reached **before** launching the F5 agent. See :ref:`Device Tunneling (VTEP) selfips` for more information.



.. _Installation Guide for Red Hat Enterprise Linux 7 and CentOS 7: http://docs.openstack.org/liberty/install-guide-rdo/environment.html
.. _Installation Guide for Ubuntu 14.04 (LTS): http://docs.openstack.org/liberty/install-guide-ubuntu/environment.html
.. _OpenStack Installation Guide for openSUSE and SUSE Linux Enterprise: http://docs.openstack.org/liberty/install-guide-obs/environment.html
.. _Nova: http://www.openstack.org/software/releases/liberty/components/nova
.. _Neutron: http://www.openstack.org/software/releases/liberty/components/neutron
.. _Keystone: http://www.openstack.org/software/releases/liberty/components/keystone
.. _Glance: http://www.openstack.org/software/releases/liberty/components/glance
.. _Horizon: http://www.openstack.org/software/releases/liberty/components/horizon
.. _Heat: http://www.openstack.org/software/releases/liberty/components/heat
.. _Barbican: http://www.openstack.org/software/releases/liberty/components/barbican
.. _license: https://f5.com/products/how-to-buy/simplified-licensing
.. _BIG-IP LTM Release Notes: https://support.f5.com/kb/en-us/search.res.html?q=+inmeta:archived%3DArchived%2520documents%2520excluded+inmeta:product%3DBIG%252DIP%2520LTM+inmeta:kb_doc_type%3DRelease%2520Note+inmeta:archived%3DArchived%2520documents%2520excluded+inmeta:BIG%252DIP%2520LTM%3D12%252E1%252E0&dnavs=inmeta:product%3DBIG%252DIP%2520LTM+inmeta:kb_doc_type%3DRelease%2520Note+inmeta:archived%3DArchived%2520documents%2520excluded+inmeta:BIG%252DIP%2520LTM%3D12%252E1%252E0&filter=p&num=
.. _RDO Packstack Quickstart: https://www.rdoproject.org/install/quickstart/
.. _LBaaSv2 dashboard panels: http://docs.openstack.org/mitaka/networking-guide/adv-config-lbaas.html#add-lbaas-panels-to-dashboard
.. _Configuring the basic BIG-IP network: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-ecmp-mirrored-clustering-12-1-0/2.html?sr=56312127
