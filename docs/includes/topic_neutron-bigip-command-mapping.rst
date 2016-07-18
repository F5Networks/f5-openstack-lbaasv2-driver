:orphan: true

F5 LBaaSv2 to BIG-IP Configuration Mapping
==========================================

Overview
--------

When you issue ``neutron lbaas`` commands on your OpenStack Neutron controller or host, the F5® LBaaSv2 driver and F5 agent configure objects on your BIG-IP® device(s). Here, we've provided some insight into what exactly happens behind the scenes to configure BIG-IP objects. You can also view the actual calls made by setting the F5 agent's DEBUG level to 'True' in the :ref:`agent configuration file` and viewing the logs (:file:`/var/log/neutron/f5-openstack-agent.log`).

.. include:: ref_neutron-to-bigip-configs-table.rst
    :start-line: 5
    :end-line: 26



The configurations applied when you issue ``neutron lbaas`` commands depend on how your BIG-IP is deployed and your network architecture. Far fewer configurations are made for an :term:`overcloud`, :term:`standalone` BIG-IP deployment than by F5 LBaaSv2 than for an :term:`undercloud` :term:`active-standby pair` or  :term:`device service cluster`.

The table below shows what happens on the BIG-IP when various commands are issued in Neutron to the F5 agent for a standalone BIG-IP deployed outside of OpenStack.


======================================     =================================================================================
Command                                    Action
======================================     =================================================================================
``systemctl start f5-openstack agent``     | - agent reads vtep interface defined in config file
                                           | - BIG-IP advertises that vtep's IP address
                                           | - the selfip IP address is discoverd by Neutron as the agent's ``tunneling_ip``
                                           | - new port for the vtep added to the OVS switch
                                           | - tunnel profiles created on BIG-IP for all tunnel types
                                           | (not limited to the ``advertised tunnel type`` setting in the config file)
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-loadbalancer-create``      | - new partition created using the prefix [#]_ and tenant ID [#]_
                                           | - fdb records added for all peers in network
                                           | - new route domain created; traffic group is inherited by default
                                           | - new self-ip created on specified subnet where the BIG-IP can receive traffic
                                           | - new tunnel created with vtep as local address (using vxlan profile created
                                           | when agent started)
                                           | - snat pool list / snat translation list created on BIG-IP (number of snat
                                           | addresses created is defined in agent config file) [#]_
                                           | - neutron port created for each snat address
                                           | - if snat mode is turned off / snat addresses set to 0, the self ip is used as
                                           | a gateway that intercepts traffic from members returning traffic back through
                                           | the BIG-IP (gateway routed mode)
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-listener-create``          | - new virtual server created in the tenant partition
                                           | - uses IP address assigned to loadbalancer by Neutron
                                           | - uses route domain created for partition when loadbalancer was created
                                           | - restricts traffic to the tunnel assigned to the loadbalancer
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-pool-create``              | - new pool created in the tenant partition, assigned to the virtual server
                                           | (or, listener) specified in the command
--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-member-create``            | - tbd

--------------------------------------     ---------------------------------------------------------------------------------
``neutron lbaas-healthmonitor-create``     | - tbd

======================================     =================================================================================






.. Further Reading
    ---------------
    .. seealso::
        * x
        * y
        * z


.. rubric:: Footnotes:
.. [#] The default prefix is "Project\_".
.. [#] Run ``openstack project list`` to get a list of configured tenant names and IDs.
.. [#] Global routed mode just uses self-ip and all traffic is directed to it automatically by some other mechanism (*needs verification*)
