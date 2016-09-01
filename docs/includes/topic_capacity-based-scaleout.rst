Capacity-Based Scale Out
````````````````````````

In a differentiated service environment, you can configure multiple F5® agents. Each of the agents is associated with a distinct iControl® endpoint (in other words, different BIG-IP® devices). When environment grouping is configured, the service provider scheduler will consider the grouping along with an ``environment_capacity_score`` reported by the agents. Together, the agent grouping and the capacity score allow the scheduler to scale out a single environment across multiple BIG-IP® device service groups.

To enable environment grouping, edit the ``environment_group_number`` setting in :file:`/etc/neutron/f5-openstack-agent.ini` (excerpt shown below).

.. code-block:: text

    # When using service differentiated environments, the environment can be
    # scaled out to multiple device service groups by providing a group number.
    # Each agent associated with a specific device service group should have
    # the same environment_group_number.
    #
    # environment_group_number = 1


All agents in the same group should have the same ``environment_group_number`` setting.

Each agent measures its BIG-IP® devices' capacity. The agent reports a single ``environment_capacity_score`` for its group every time it reports its status to the Neutron controller.

The ``environment_capacity_score`` value is the highest capacity recorded on several collected statistics specified in the ``capacity_policy`` setting in the agent configuration. The ``capacity_policy`` setting is a dictionary, where the key is the metric name and the value is the max allowed value for that metric. The score is determined by dividing the metric collected by the max specified for that metric in the ``capacity_policy`` setting. An acceptable reported ``environment_capacity_score`` is between zero (0) and one (1). **If an agent in the group reports an ``environment_capacity_score`` of one (1) or greater, the device is considered to be at capacity.**

.. code-block:: shell

    # capacity_policy = throughput:1000000000, active_connections: 250000, route_domain_count: 512, tunnel_count: 2048


.. warning::

    If you set the ``capacity_policy`` and all agents in all groups for an environment are at capacity, services will no longer be scheduled. When pools are created for an environment which has no capacity left, the pools will be placed in the error state.


The following metrics implemented by the iControl® driver can also be configured in :file:`/etc/neutron/f5-openstack-agent.ini`.

.. code-block:: shell

    # throughput - total throughput in bps of the TMOS devices
    # inbound_throughput - throughput in bps inbound to TMOS devices
    # outbound_throughput - throughput in bps outbound from TMOS devices
    # active_connections - number of concurrent active actions on a TMOS device
    # tenant_count - number of tenants associated with a TMOS device
    # node_count - number of nodes provisioned on a TMOS device
    # route_domain_count - number of route domains on a TMOS device
    # vlan_count - number of VLANs on a TMOS device
    # tunnel_count - number of GRE and VxLAN overlay tunnels on a TMOS device
    # ssltps - the current measured SSL TPS count on a TMOS device
    # clientssl_profile_count - the number of clientside SSL profiles defined
    #
    # You can specify one or multiple metrics.


When you create a new pool in an environment where multiple agent groups are configured, and the pool's ``tenant_id`` is not already associated with an agent group, the scheduler will attempt to assign the pool to the agent group which last reported the lowest ``environment_capacity_score``. If the pool's ``tenant_id`` is already associated with an agent group that is at capacity, the scheduler binds the pool to an agent in another group in the environment that is not at capacity.
