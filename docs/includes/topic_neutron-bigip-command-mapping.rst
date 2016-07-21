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
``systemctl start f5-openstack agent``     | 1. agent reads vtep self IP defined in config file
                                           | 2. BIG-IP advertises that vtep's IP address
                                           | 3. the selfip IP address is advertised to Neutron as the agent's
                                           | ``tunneling_ip``
                                           | 4. new port for the vtep added to the OVS switch
                                           | 5. tunnel profiles created on BIG-IP for all tunnel types
                                           | (not just for the ``advertised tunnel type`` setting in the config file) [#]_
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-loadbalancer-create``      | 1. new partition created using the prefix [#]_ and tenant ID [#]_
                                           | 2. fdb records added for all peers in network
                                           | 3. new route domain created
                                           | 4. new self-ip created on specified subnet where the BIG-IP can receive traffic
                                           | 5. new tunnel created with vtep as local address (using vxlan profile created
                                           | when agent started) [#]_
                                           | 6. snat pool list / snat translation list created on BIG-IP (number of snat
                                           | addresses created is defined in agent config file) [#]_
                                           | 7. neutron port created for each snat address
                                           |    - if snat mode is turned off / snat addresses is set to ``0``, the BIG-IP
                                           |    acts as a gateway so that return traffic from members is routed through it
                                           |    - if snat mode is turned on / snat addresses is set to ``0``, auto snat
                                           |    mode is used
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-listener-create``          | 1. new virtual server created in the tenant partition
                                           |    - attempts to use Fast L4 by default
                                           |    - if persistence is configured, Standard is used
                                           |    - uses IP address assigned to loadbalancer by Neutron
                                           |    - uses route domain created for partition when loadbalancer was created
                                           |    - restricts traffic to the tunnel assigned to the loadbalancer
                                           |
                                           | If the ``--protocol`` is ``TERMINATED_HTTPS``: [#]_
                                           |    - certificate/key container fetched from Barbican using the URI defined by
                                           |    ``default_tls_container_ref`` option
                                           |    - key and certificate imported to BIG-IP
                                           |    - custom SSL profile created using ``clientssl`` as the parent profile
                                           |    - SSL profile add to the virtual server
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-pool-create``              | 1. new pool created in the tenant partition
                                           |    - assigned to the virtual server (or, listener) specified in the command
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-member-create``            | - coming soon

--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-healthmonitor-create``     | - coming soon

======================================     =================================================================================



https listener
 - custom profile created; inherits settings from the [client-? or server-?] SSL profile


.. Further Reading
    ---------------
    .. seealso::
        * x
        * y
        * z


.. rubric:: Footnotes:
.. [#] :ref:`L2 Segmentation Mode Settings` --> ``advertised_tunnel_types``
.. [#] :ref:`Environment Settings` --> ``environment_prefix`` The default prefix is "Project".
.. [#] Run ``openstack project list`` to get a list of configured tenant names and IDs.
.. [#] If using :ref:`global routed mode`, all traffic is directed to the self IP (no tunnel created)
.. [#] :ref:`L3 Segmentation Mode Settings` --> ``f5_snat_addresses_per_subnet``
.. [#] see :ref:`Certificate Manager / SSL Offloading`
