:orphan: true

Managing BIG-IP Clusters
========================

Overview
--------

The F5® LBaaSv2 agent and driver can manage BIG-IP® :term:`device service clusters`, providing :term:`high availability`, :term:`mirroring`, and :term:`failover` services within your OpenStack cloud.

The F5 agent applies LBaaS configuration changes to each BIG-IP :term:`device` in a cluster at the same time, in real time. This is referred to in the :ref:`Agent Configuration File` as ``replication mode``. Replication mode makes it unnecessary to use  BIG-IP's '`configuration synchronization`_ mode' for LBaaS objects managed by the agent.

Use Case
--------

Clustering provides a greater degree of redundancy than a standalone device offers. It helps to avoid service interruptions that could otherwise occur if a device should go down. A few commonly-used BIG-IP clustering examples are `Sync-Failover device groups`_ and `Sync-Only device groups`_.


Prerequisites
-------------

- Basic understanding of `BIG-IP® device service clustering <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html>`_.

- Licensed, operational BIG-IP :term:`device service cluster`. [#]_

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <install-f5-lbaasv2-driver>` installed on the Neutron controller and all other hosts for which you want to provision LBaaS services.

Caveats
-------

- Clusters of more than two (2) BIG-IP devices are not supported in this release (v |release|).


Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini


2. Set the :ref:`HA mode` to :term:`pair` or :term:`scalen`.

.. code-block:: text
    :emphasize-lines: 10

    # HA mode
    #
    # Device can be required to be:
    #
    # standalone - single device no HA
    # pair - active/standby two device HA
    # scalen - active device cluster
    #
    #
    f5_ha_type = pair
    #
    #


.. Further Reading
    --------------


.. rubric:: Footnotes

..[#] You can use the following F5 Heat templates to prep and deploy an overcloud :term:`active-standby` cluster: :ref:`heat:F5® BIG-IP® VE: Cluster-Ready, 4-nic`; :ref:`heat:F5® BIG-IP®: Active-Standby Cluster`



.. _BIG-IP device service clustering: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html

.. _BIG-IP Device Service Clustering -- Administration guide: <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html

.. _Sync-Failover device groups: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/5.html#unique_457113521

.. _Sync-Only device groups: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/5.html#unique_558181421

.. _configuration synchronization: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/6.html#unique_1589362110
