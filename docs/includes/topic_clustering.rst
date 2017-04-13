:orphan: true

Manage BIG-IP Clusters with F5 LBaaSv2
======================================

Overview
--------

The F5 LBaaSv2 agent and driver can manage BIG-IP :term:`device service clusters`, providing :term:`high availability`, :term:`mirroring`, and :term:`failover` services within your OpenStack cloud.

The F5 agent applies LBaaS configuration changes to each BIG-IP :term:`device` in a cluster at the same time, in real time. It is unnecessary to use BIG-IP's '`configuration synchronization`_ mode' to sync LBaaS objects managed by the agent across the devices in a cluster.

Clustering provides a greater degree of redundancy than a standalone device offers. It helps to avoid service interruptions that could otherwise occur if a device should go down. F5 LBaaSv2 can manage BIG-IP `Sync-Failover device groups`_ when set to use either the :term:`pair` or the :term:`scalen` :ref:`High Availability mode <HA mode>`.

    .. figure:: ../media/f5-lbaas-scalen-cluster.png
        :alt: BIG-IP scalen cluster
        :width: 500

        BIG-IP scalen cluster

.. important::

    The F5 agent expects to find a specific number of entries for the ``icontrol_hostname`` parameter based on the configured ``f5_ha_type``, as noted below.

    .. list-table::
        :header-rows: 1

        * - ha type
          - number of iControl endpoints
        * - standalone
          - 1
        * - pair
          - 2
        * - scalen
          - > 2

F5 LBaaSv2 and BIG-IP Auto-sync
```````````````````````````````

By design, F5 LBaaSv2 applies configuration directly to each device in a cluster or pair. Because of this functionality, we do not support the use of F5 LBaaSv2 with BIG-IP device clusters that are set to use auto-sync. If, for example, you create a load balancer for a device group that is set to use auto-sync, the create command will only succeed on the first device in the group; it will fail on the others because the object will have already been created via auto-sync.

For this reason, we recommend manually syncing BIG-IP device groups after making configuration changes with F5 LBaaSv2.

.. caution::

    If you choose to enter only one (1) iControl endpoint for your device group and rely on auto-sync, you must set the ``f5_ha_type`` to ``standalone``. Should you choose to do so, however, **you will need to manually update** the :ref:`agent configuration file` with the iControl endpoint of another device in the group should the configured device fail.

    While it is possible to use auto-sync for a device group *after* creating a new load balancer, it is not recommended. This functionality has not been tested.

Prerequisites
-------------

- Basic understanding of `BIG-IP device service clustering <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html>`_.

- Licensed, operational BIG-IP :term:`device service cluster`.

    .. tip::

        If you do not already have a BIG-IP cluster deployed in your network, you can use the `F5 BIG-IP: Active-Standby Cluster <http://f5-openstack-heat.readthedocs.io/en/latest/templates/supported/ref_f5-plugins_active-standby.html>`_ Heat template to create a two-device cluster.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP devices and OpenStack cloud.

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` installed on the Neutron controller and all other hosts from which you want to provision LBaaS services.


Caveats
-------

- The F5 agent can manage clusters of two (2) to four (4) BIG-IP devices. Active-standby mode can only be used with two (2) devices; scalen is used with clusters of more than two devices.

- The administrator login must be the same on all BIG-IP devices in the cluster.

Configuration
-------------

#. Edit the :ref:`Agent Configuration File`:

    .. code-block:: text

        $ sudo vi /etc/neutron/services/f5/f5-openstack-agent.ini


#. Set the :ref:`HA mode` to :term:`pair` or :term:`scalen`.

    .. code-block:: text
        :emphasize-lines: 10

        # HA mode
        #
        # Device can be required to be:
        #
        # standalone - single device no HA
        # pair - active-standby two device HA
        # scalen - active device cluster
        #
        #
        f5_ha_type = pair
        #
        #

#. Add the IP address for each BIG-IP device, the admin username, and the admin password to the :ref:`Device Driver - iControl Driver Setting <Device Driver Settings / iControl Driver Settings>` section of the config file. Values must be comma-separated.

    .. code-block:: text
        :emphasize-lines: 10

        #
        icontrol_hostname = 10.190.7.232,10.190.4.193
        #
        icontrol_username = admin
        #
        icontrol_password = admin
        #


Further Reading
---------------

.. seealso::

    * `BIG-IP Device Service Clustering -- Administration Guide`_





.. _BIG-IP device service clustering: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html

.. _BIG-IP Device Service Clustering -- Administration guide: <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html

.. _Sync-Failover device groups: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/5.html#unique_457113521

.. _configuration synchronization: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/6.html#unique_1589362110
