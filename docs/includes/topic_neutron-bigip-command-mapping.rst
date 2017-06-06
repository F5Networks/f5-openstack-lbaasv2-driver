:orphan: true

F5 LBaaSv2 to BIG-IP Configuration Mapping
==========================================

Overview
--------

When you issue ``neutron lbaas`` commands on your OpenStack Neutron controller or host, the F5® LBaaSv2 driver and F5 agent configure objects on your BIG-IP® device(s). Here, we've provided some insight into what exactly happens behind the scenes to configure BIG-IP objects. You can also view the actual calls made by setting the F5 agent's DEBUG level to 'True' in the :ref:`agent configuration file` and viewing the logs (:file:`/var/log/neutron/f5-openstack-agent.log`).

.. include:: ref_neutron-to-bigip-configs-table.rst
   :start-line: 5
   :end-line: 26



The configurations applied when you issue ``neutron lbaas`` commands depend on how your BIG-IP is deployed and your network architecture. Far fewer configurations are made for an :term:`overcloud`, :term:`standalone` BIG-IP deployment than for an :term:`undercloud` :term:`active-standby pair` or :term:`device service cluster`.

The table below shows what happens on the BIG-IP when various commands are issued in Neutron to the F5 agent for a standalone, overcloud BIG-IP.


======================================     =================================================================================
Command                                    Action
======================================     =================================================================================
``systemctl start f5-openstack agent``     | 1. Agent reads the vtep `self IP`_ defined in the agent config file.
                                           | 2. BIG-IP advertises the vtep's IP address.
                                           | 3. The self IP address is advertised to Neutron as the agent's
                                           | ``tunneling_ip``.
                                           | 4. A new port for the vtep is added to the OVS switch.
                                           | 5. Profiles for all tunnel types are created on the BIG-IP. [#]_
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-loadbalancer-create``      | 1. A new partition is created using the prefix [#]_ and tenant ID [#]_.
                                           | 2. New fdb records are added for all peers in the network.
                                           | 3. A new route domain is created.
                                           | 4. A new self IP where the BIG-IP can receive traffic is created on the
                                           | specified subnet.
                                           | 5. A new tunnel is created, using the vtep as the local address (uses the
                                           | vxlan profile created when the agent was first started). [#]_
                                           | 6. A SNAT pool list / SNAT translation list is created on the BIG-IP.
                                           |    - The number of SNAT addresses that will be created is defined in the agent
                                           |    config file. [#]_
                                           | 7. A neutron port is created for each SNAT address.
                                           |    - If SNAT mode is turned off and SNAT addresses is set to ``0``, the BIG-IP
                                           |    will act as a gateway so return traffic from members is always routed
                                           |    through it.
                                           |    - If SNAT mode is turned on & SNAT addresses is set to ``0``, `SNAT automap`_
                                           |    will be used.
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-listener-create``          | 1. A new virtual server is created in the tenant partition on the BIG-IP.
                                           |    - Attempts to use Fast L4 by default.
                                           |    - If persistence is configured, Standard is used.
                                           |    - Uses the IP address assigned to the load balancer by Neutron.
                                           |    - Uses the route domain that was created for the new partition when the
                                           |    load balancer was created.
                                           |    - Traffic is restricted to the tunnel assigned to the load balancer.
                                           |
                                           | If the listener ``--protocol`` is ``TERMINATED_HTTPS``: [#]_
                                           |    - The certificate/key container is fetched from Barbican using the URI
                                           |    defined by the ``default_tls_container_ref`` config option.
                                           |    - The key and certificate are imported to the BIG-IP.
                                           |    - A custom SSL profile is created using ``clientssl`` as the parent profile.
                                           |    - The SSL profile is added to the virtual server.
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-pool-create``              | 1. A new pool is created in the tenant partition on the BIG-IP.
                                           |    - It is assigned to the virtual server (or, listener) specified in the
                                           |    command.
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-member-create``            | 1. A new member is created in the specified pool using the IP address and
                                           |    subnet supplied in the command.
                                           |    - If the member is the first created for the specified pool, the pool
                                           |    status will change on the BIG-IP.
                                           |    - If the member is the first created with the supplied IP address, a new
                                           |    node is also created.
                                           |    - If the member's IP address and subnet correspond to an existing Neutron
                                           |      port, the agent creates a forwarding database (FDB) entry for the member
                                           |      on the BIG-IP device(s). [#tablefn7]_
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-healthmonitor-create``     | 1. A new health monitor is created on the BIG-IP for the specified pool.
                                           |    - If the health monitor is the first created for the specified pool, the
                                           |    pool status will change on the BIG-IP.
                                           |    - Health monitors directly affect the status and availability of pools and
                                           |    members on the BIG-IP. Any additions or changes may result in a status
                                           |    change for the specified pool.
======================================     =================================================================================



Further Reading
---------------
.. seealso::

    * `OpenStack Neutron CLI Reference <http://docs.openstack.org/cli-reference/neutron.html>`_
    * `BIG-IP Local Traffic Management - Basics <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-1-0.html?sr=55917227>`_



.. rubric:: Footnotes:
.. [#] This is done for all tunnel types, not just those configured as the ``advertised_tunnel_types`` in the :ref:`L2 Segmentation Mode` Settings.
.. [#] Configured in ``Environment Settings --> environment_prefix``. The default prefix is ``Project``.
.. [#] Run ``openstack project list`` to get a list of configured tenant names and IDs.
.. [#] If using :ref:`global routed mode`, all traffic is directed to the self IP (no tunnel is created).
.. [#] Configured in :ref:`L3 Segmentation Mode` Settings --> ``f5_snat_addresses_per_subnet``.
.. [#] See :ref:`Certificate Manager / SSL Offloading`.
.. [#tablefn7] If the pool member does not have a corresponding Neutron port, warnings will print to the :code:`f5-openstack-agent` and :code:`neutron-server` log; the agent **will not** create an FDB entry for the member on the BIG-IP device(s).

.. _self IP: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/6.html#conceptid
.. _SNAT automap: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/8.html#unique_375712497
