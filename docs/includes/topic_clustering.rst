.. orphan::

Managing BIG-IP Clusters
========================

Overview
--------

The F5® LBaaSv2 agent and driver can manage BIG-IP® device service clusters (or just 'clusters', for short), providing high availability, mirroring, and failover capabilities from within your OpenStack cloud. The F5 agent applies LBaaS configuration changes to each BIG-IP device in a cluster at the same time, in real time. This is referred to in the :ref:`Agent Configuration File` as ``replication mode``.

Use Case
--------

Generally, clusters are used by :ref:`undercloud` BIG-IP deployments which may contain :ref:`multiple tenants <multi-tenancy>`.



Prerequisites
-------------

- An existing, functional BIG-IP device service cluster.

    .. seealso::

        The following F5 Heat templates can be used to prep and deploy an :term:`active-standby` cluster:

        - :ref:`heat:F5® BIG-IP® VE: Cluster-Ready, 4-nic`
        - :ref:`heat:F5® BIG-IP®: Active-Standby Cluster`



Caveats
-------

- Currently, only clusters of two (2) BIG-IP devices are supported.
-
-


Configuration
-------------


1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini


2. Set the :ref:`HA mode` to `pair` or `scalen`.

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




Further Reading
---------------

.. seealso::

    * `BIG-IP Device Service Clustering -- Administration guide`_
    *
    * z


.. _BIG-IP Device Service Clustering -- Administration guide: <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html