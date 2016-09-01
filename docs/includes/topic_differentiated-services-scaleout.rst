Differentiated Services and Scale Out
-------------------------------------

The F5® LBaaSv2 plugin supports deployments where multiple BIG-IP® environments are required. In a differentiated service environment, each F5® driver will work as described above **with the exception** that each environment has its own messaging queue. The Tenant scheduler for each environment only considers agents within that environment. Configuring multiple environments with corresponding distinct ``neutron_lbaas`` service provider entries is the only way to allow a tenant to select its environment through the LBaaS API. The first section of :file:`/etc/neutron/services/f5/f5-openstack-agent.ini` provides information regarding configuration of multiple environments.

.. topic:: To configure differentiated LBaaSv2 provisioning:

    1. Install the agent and driver on each host that requires LBaaSv2 provisioning.

    2. Assign the agent an environment-specific name in :file:`/etc/neutron/services/f5/f5-openstack-agent.ini`.

    3. Create a service provider entry for each agent in :file:`/etc/neutron/neutron_lbaas` that corresponds to the unique agent name you assigned.

.. warning::

    A differentiated BIG-IP® environment can not share anything.


