:orphan: true

Agent Redundancy and Scale Out
==============================

Overview
--------

.. important::

    We refer to 'hosts' a lot in this document. A 'host' could be a Neutron controller, a compute node, a container, etc.; the important takeaway is that in order to run multiple agents in one environment, **each agent must have a unique** ``hostname``. [#]_

When the Neutron LBaaS plugin loads the F5 LBaaSv2 driver, it creates a global messaging queue to be used for all callbacks and status update requests from F5 LBaaSv2 agents. Requests are passed from the global messaging queue to F5 LBaaSv2 drivers in a round-robin fashion, then passed on to an F5 agent as described in the :ref:`Agent-Tenant Affinity` section.

Agent-Tenant Affinity
`````````````````````

The F5 LBaaSv2 agent scheduler uses the Neutron database and 'agent-tenant affinity' to determine which F5 agent should handle an LBaaS request.

How it works:

#. The Neutron controller receives a new ``loadbalancer`` request.
#. The F5 LBaaSv2 agent scheduler consults the Neutron database to determine if any F5 agent is already bound to the load balancer to which the request applies.
#. If the scheduler finds a bound agent, it assigns the request to that agent.
#. If the scheduler doesn't find a bound agent, it checks the load balancer's ``tenant_id`` to determine if any agent has already handled a request for that tenant (in other words, has affinity with that tenant, or 'agent-tenant affinity').
#. If the scheduler finds an agent that has affinity with the load balancer's tenant, it selects that agent to complete the request.
#. If the scheduler doesn't find an agent that either is bound to the load balancer or has affinity with the load balancer's ``tenant_id``, it selects an active agent at random.

    * The selected agent is then bound to the load balancer and handles all future LBaaS requests associated with it.

#. If the agent bound to the load balancer is inactive, the scheduler looks for other active agents in the same group as the 'dead' agent and assigns the task to the first one it finds. The load balancer remains bound to the original agent, with the expectation that the agent will eventually come back online.

.. warning::

    If you delete an agent, you should also delete all load balancers bound to that agent.

    To view all load balancers associated with a specific agent:

    .. code-block:: bash

        $ neutron lbaas-loadbalancer-list-on-agent <agent-id>


Use Case
--------

You can run multiple F5 agents **on different hosts** in your OpenStack cloud to provide agent redundancy and scale-out. Managing the same BIG-IP device or cluster from different hosts ensures that if one host goes down, the F5 LBaaSv2 processes remain alive and functional. It also allows you to spread the request load for the environment across multiple agents.

You can run multiple F5 agents on the same host only if they are each managing a different BIG-IP


Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.
- Operational OpenStack cloud (|openstack| release).
- Administrator access to both the BIG-IP device(s) and the OpenStack cloud.
- All hosts running F5 LBaaSv2 must have the Neutron and Neutron LBaaS packages installed.
- All hosts running F5 LBaaSv2 must use the same Neutron database.


Caveats
-------

- You **can not** run multiple agents on the same host if they are expected to manage the same BIG-IP device or :term:`cluster`. See :ref:`Differentiated Service Environments` for information about running more than one F5 agent/driver on the same host.
- In the standard multi-agent deployment, specifying the F5 agent/BIG-IP pair to use when creating a new load balancer is not supported. Instead, use a custom environment as described in :ref:`Multiple Agents and Differentiated Service Environments`.


Configuration
-------------

To manage one BIG-IP device or device service group with multiple F5 agents, deploy F5 LBaaSv2 on separate hosts using the instructions provided below.

#. Copy the Neutron config file from your Neutron controller to each host on which you will run F5 LBaaSv2:

    .. code-block:: bash

        $ sudo cp /etc/neutron/neutron.conf <openstack_host>:/etc/neutron/neutron.conf

#. :ref:`Install the F5 Agent` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` on each host.

#. :ref:`Configure the F5 agent <Configure the F5 OpenStack Agent>` on each host.

    .. tip::

        * Be sure to provide the iControl endpoints for all BIG-IP devices you'd like the agents to manage.
        * You can configure the F5 agent once, on the Neutron controller, then copy the agent config file (:file:`/etc/neutron/services/f5/f5-openstack-agent.ini`) over to the other hosts.

#. :ref:`Start the F5 agent` on each host.



Further Reading
---------------

.. seealso::

    * :ref:`Configure the F5 OpenStack Agent`
    * :ref:`Manage BIG-IP Clusters with F5 LBaaSv2`
    * :ref:`Manage Multi-Tenant BIG-IP Devices with F5 LBaaSv2`
    * :ref:`Differentiated Service Environments`
    * :ref:`Multiple Agents and Differentiated Service Environments`


.. [#] **F5 Networks does not provide support for container service deployments.** If you are already well versed in containerized environments, you can run one F5 agent per container. The neutron.conf file must be present in the container. The service provider driver does not need to run in the container; rather, it only needs to be in the container's build context.

