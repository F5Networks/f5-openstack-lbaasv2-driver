Troubleshooting the F5® OpenStack Agent
---------------------------------------

F5® Agent is not running
~~~~~~~~~~~~~~~~~~~~~~~~

If ``f5-openstack-agent`` doesn't appear in the Horizon agent list, or when you run ``neutron agent-list``, the agent is not running.

Here are a few things you can try:

1. Check the logs:

    .. code-block:: text

        $ less /var/log/neutron/f5-openstack-agent.log

2. Check the status of the f5-openstack-agent service:

    .. code-block:: text

        $ sudo service f5-oslbaasv2-agent status           \\ Debian/Ubuntu
        $ sudo systemctl status f5-openstack-agent.service \\ RedHat/CentOS


3. Make sure you can connect to the BIG-IP® and that the iControl® hostname, username, and password in the config file are correct.


4. If you're using ``global_routed_mode``, comment out (#) the ``vtep`` lines (shown below) in the agent config file.

    .. code-block:: text

        #
        #f5_vtep_folder = 'Common'
        #f5_vtep_selfip_name = 'vtep'
        #

5. If you're using L2 segmentation, make sure the ``advertised_tunnel_types`` setting matches the ``provider:network_type``.

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


F5® Agent is not provisioning LBaaS tasks correctly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Make sure you don't have more than one agent running on the same host.

    If you see more than one entry for ``f5-openstack-agent`` and you haven't configured your host to use multiple agents, you'll need to deactivate one of them. The commands below may help you to identify which agent to deactivate.

    .. code-block:: text

        $ neutron agent-list
        \\ list all running agents

        $ neutron agent-show <agent_id>
        \\ show the details for a specific agent

        $ neutron lbaas-loadbalancer-list-on-agent <agent_id>
        \\ list the loadbalancers on the agent.

        $ neutron lbaas-loadbalancer-show <loadbalancer_id>
        \\ Show the details for a specific loadbalancer

