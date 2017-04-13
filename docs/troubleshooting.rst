Troubleshooting
===============

.. tip::

    If you can't find objects on your BIG-IP that you created using F5 LBaaSv2, check your partition. By default, all objects are created in a partition that is named with the OpenStack tenant ID and the preface 'Project\_'.

    Example: ``Project_9572afc14db14c8a806d8c8219446e7b``


Set Logging Level to DEBUG
--------------------------

To troubleshoot general problems, set the Neutron and the F5 agent ``debug`` setting to ``True``.

Extensive logging will then appear in the ``neutron-server`` and ``f5-oslbaasv1-agent`` log files on their respective hosts.

.. topic:: Set the DEBUG log level output for the f5-openstack-agent:

    .. code-block:: text

        $ sudo vi /etc/neutron/services/f5/f5-openstack-agent.ini

        #
        [DEFAULT]
        # Show debugging output in log (sets DEBUG log level output).
        debug = True
        ...


.. topic:: Set the DEBUG log level output for Neutron:

    .. code-block:: text

        $ sudo vi /etc/neutron/neutron.conf
        [DEFAULT]
        ...
        # Print debugging output (set logging level to DEBUG instead of default WARNING level).
        debug = True


F5 agent is not running
-----------------------

If ``f5-openstack-agent`` or ``f5-oslbaasv2-agent`` doesn't appear in the Horizon agent list, or when you run ``neutron agent-list``, the agent is not running.

Here are a few things you can try:

1. Check the logs:

    .. code-block:: text

        $ less /var/log/neutron/f5-openstack-agent.log

2. Check the status of the f5-openstack-agent service:

    .. code-block:: text

        $ sudo systemctl status f5-openstack-agent.service \\ CentOS
        $ sudo service f5-oslbaasv2-agent status           \\ Ubuntu


3. Make sure you can connect to the BIG-IP and that the iControl hostname, username, and password in the :ref:`agent configuration file` are correct.

4. If you're using ``global_routed_mode``, comment out (#) the ``vtep`` lines (shown below) in the :ref:`agent configuration file`.

    .. code-block:: text

        #
        #f5_vtep_folder = 'Common'
        #f5_vtep_selfip_name = 'vtep'
        #

5. If you're using L2 segmentation, make sure the ``advertised_tunnel_types`` setting from the :ref:`agent configuration file` matches the ``provider:network_type`` displayed for the network in Neutron. If it doesn't, the network may be configured incorrectly.

    .. code-block:: text
        :emphasize-lines: 9

        $ neutron net-show <network_name>
        +---------------------------+--------------------------------------+
        | Field                     | Value                                |
        +---------------------------+--------------------------------------+
        | admin_state_up            | True                                 |
        | id                        | 05f61e74-37e0-4c30-a664-762dfef1a221 |
        | mtu                       | 0                                    |
        | name                      | bigip_external                       |
        | provider:network_type     | vxlan                                |
        | provider:physical_network |                                      |
        | provider:segmentation_id  | 84                                   |
        | router:external           | False                                |
        | shared                    | False                                |
        | status                    | ACTIVE                               |
        | subnets                   |                                      |
        | tenant_id                 | 1a35d6558b59423e83f4500f1ebc1cec     |
        +---------------------------+--------------------------------------+


F5 agent is not provisioning LBaaS tasks correctly
--------------------------------------------------

1. Make sure you don't have more than one agent running on the same host.

    If you see more than one entry for ``f5-openstack-agent`` or ``f5-oslbaasv2-agent`` and you haven't configured your host to use multiple agents, you'll need to deactivate one of them. The commands below may help you to identify which agent to deactivate.

    .. code-block:: text

        $ neutron agent-list
        \\ list all running agents

        $ neutron agent-show <agent_id>
        \\ show the details for a specific agent

        $ neutron lbaas-loadbalancer-list-on-agent <agent_id>
        \\ list the loadbalancers on the agent.

        $ neutron lbaas-loadbalancer-show <loadbalancer_id>
        \\ show the details for a specific load balancer


2. Make sure you're not running LBaaSv1 and LBaaSv2 at the same time.

    In the :ref:`Neutron configuration file <configure-neutron-lbaasv2>` (:file:`/etc/neutron/neutron.conf`), remove the entry for the lbaasv1 plugin, if it exists.

    **Correct**

    .. code-block:: text

        service_plugins = router,lbaasv2
        \\ OR \\
        service_plugins = router,neutron_lbaas.services.loadbalancer.plugin.LoadBalancerPluginv2


    **Incorrect**

    .. code-block:: text

        service_plugins = router,lbaas,lbaasv2


    In the Neutron LBaaS configuration file (:file:`/etc/neutron/neutron_lbaas.conf`), remove or comment out (#) the entry for the F5 LBaaSv1 service provider driver.

    .. code-block:: text
        :emphasize-lines: 2, 9

        [service_providers]
        service_provider = LOADBALANCERV2:F5Networks:neutron_lbaas.drivers.f5.driver_v2.F5LBaaSV2Driver:default
        # Must be in form:
        # service_provider = <service_type>:<name>:<driver>[:default]
        # List of allowed service types includes LOADBALANCER
        # Combination of <service type> and <name> must be unique; <driver> must also be unique
        # This is multiline option
        # service_provider = LOADBALANCER:name:lbaas_plugin_driver_path:default
        # service_provider = LOADBALANCER:F5:f5.oslbaasv1driver.drivers.plugin_driver.F5PluginDriver:default
        # service_provider = LOADBALANCER:Haproxy:neutron_lbaas.services.loadbalancer.drivers.haproxy.plugin_driver.HaproxyOnHostPluginDriver:default
        # service_provider = LOADBALANCER:radware:neutron_lbaas.services.loadbalancer.drivers.radware.driver.LoadBalancerDriver:default
        # service_provider = LOADBALANCER:NetScaler:neutron_lbaas.services.loadbalancer.drivers.netscaler.netscaler_driver.NetScalerPluginDriver
        # service_provider = LOADBALANCER:Embrane:neutron_lbaas.services.loadbalancer.drivers.embrane.driver.EmbraneLbaas:default
        # service_provider = LOADBALANCER:A10Networks:neutron_lbaas.services.loadbalancer.drivers.a10networks.driver_v1.ThunderDriver:default
        # service_provider = LOADBALANCER:VMWareEdge:neutron_lbaas.services.loadbalancer.drivers.vmware.edge_driver.EdgeLoadbalancerDriver:default

        # LBaaS v2 drivers
        # service_provider = LOADBALANCERV2:Octavia:neutron_lbaas.drivers.octavia.driver.OctaviaDriver:default
        # service_provider = LOADBALANCERV2:radwarev2:neutron_lbaas.drivers.radware.v2_driver.RadwareLBaaSV2Driver:default
        # service_provider = LOADBALANCERV2:LoggingNoop:neutron_lbaas.drivers.logging_noop.driver.LoggingNoopLoadBalancerDriver:default
        # service_provider = LOADBALANCERV2:Haproxy:neutron_lbaas.drivers.haproxy.plugin_driver.HaproxyOnHostPluginDriver:default
        # service_provider = LOADBALANCERV2:A10Networks:neutron_lbaas.drivers.a10networks.driver_v2.ThunderDriver:default
        # service_provider = LOADBALANCERV2:brocade:neutron_lbaas.drivers.brocade.driver_v2.BrocadeLoadBalancerDriver:default
        # service_provider = LOADBALANCERV2:kemptechnologies:neutron_lbaas.drivers.kemptechnologies.driver_v2.KempLoadMasterDriver:default


VxLAN traffic is not reaching BIG-IP
------------------------------------

1. Make sure the vtep endpoint identified in the :ref:`agent configuration file` is set to 'Allow All'.

    The default setting for `port lockdown behavior`_ does not include VxLAN traffic. Setting the vtep to 'Allow All' will ensure that VxLAN traffic from the OpenStack cloud is not blocked by the BIG-IP.

2. Check the VxLAN port binding.

    If you're using the default Open vSwitch (ovs) core plugin, you can run the command ``ovs-vsctl show`` to view a list of configured bridges and associated ports. As shown in the example below, there should be a ``remote_ip`` address for a VxLAN tunnel that corresponds to the self IP identified in the :ref:`agent configuration file`.

    **Example**: The code blocks below demonstrate that the ovs ``br-tun`` interface contains a port on which the ``remote_ip`` address matches that of the ``vtep`` self IP.

    .. code-block:: text
        :emphasize-lines: 1, 17

        [user@host-19 ~(keystone_user)]$ sudo ovs-vsctl show
        f08cd9da-cf33-4bc6-bdd2-960caed1136c
        Bridge br-ex
            ...
        Bridge br-tun
            fail_mode: secure
            Port "vxlan-c9001901"
                Interface "vxlan-c9001901"
                    type: vxlan
                    options: {df_default="true", in_key=flow, local_ip="201.0.20.1", out_key=flow, remote_ip="201.0.25.1"}
            Port br-tun
                Interface br-tun
                    type: internal
            Port "vxlan-0a020264"
                Interface "vxlan-0a020264"
                    type: vxlan
                    options: {df_default="true", in_key=flow, local_ip="201.0.20.1", out_key=flow, remote_ip="10.2.2.100"}
            Port patch-int
                Interface patch-int
                    type: patch
                    options: {peer=patch-tun}
            Port "gre-c9001901"
                Interface "gre-c9001901"
                    type: gre
                    options: {df_default="true", in_key=flow, local_ip="201.0.20.1", out_key=flow, remote_ip="201.0.25.1"}
            Port "vxlan-c9001801"
                Interface "vxlan-c9001801"
                    type: vxlan
                    options: {df_default="true", in_key=flow, local_ip="201.0.20.1", out_key=flow, remote_ip="201.0.24.1"}
            Port "gre-c9001801"
                Interface "gre-c9001801"
                    type: gre
                    options: {df_default="true", in_key=flow, local_ip="201.0.20.1", out_key=flow, remote_ip="201.0.24.1"}
        Bridge br-int
            ...
        ovs_version: "2.5.0"

\
    .. code-block:: text
        :emphasize-lines: 3

        root@(localhost)(cfg-sync Standalone)(Active)(/Common)(tmos.net)# list self vtep
        net self vtep {
            address 10.2.2.100/16
            allow-service all
            traffic-group traffic-group-local-only
            vlan external
        }




.. _port lockdown behavior: https://support.f5.com/kb/en-us/solutions/public/17000/300/sol17333.html
