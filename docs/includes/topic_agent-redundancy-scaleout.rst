:orphan: true

Agent Redundancy and Scale-out
==============================

Overview
--------

The F5® LBaaSv2 driver runs within the Neutron controller. When the Neutron LBaaS plugin loads the driver, it creates a global messaging queue to be used for all callbacks and status update requests from F5 LBaaSv2 agents.

.. important::

    We refer to 'hosts' a lot in this document. A 'host' could be a Neutron controller, a server, a Docker container, etc.; the important takeaway is that in order to run multiple agents in one environment, **each agent must have a unique** ``hostname``.


Use Case
--------

You can run multiple F5 agents **on different hosts** in your OpenStack cloud to provide agent redundancy and scale-out. Managing the same BIG-IP device or cluster from different hosts ensures that if one host goes down, the F5 LBaaSv2 processes remain alive and functional. It also allows you to spread the request load for the environment across multiple agents.

All F5 LBaaSv2 drivers consult the same messaging queues to pass requests to their respective agents; the message queue corresponds to the ``environment_prefix`` configured in the F5 agent ``.ini`` file. Requests are passed from the global messaging queue to F5 LBaaSv2 drivers in a round-robin fashion, then passed on to an F5 agent as described below.

Agent-Tenant Affinity
`````````````````````

The F5 LBaaSv2 agent scheduler uses the Neutron database and 'agent-tenant affinity' to determine which F5 agent should handle an LBaaS request.

How it works:

#. The Neutron controller receives a new ``loadbalancer`` request.
#. The F5 LBaaSv2 agent scheduler consults the Neutron database to determine if any F5 agent is already bound to the loadbalancer to which the request applies.
#. If the scheduler finds a bound agent, it assigns the request to that agent.
#. If the scheduler doesn't find a bound agent, it checks the loadbalancer's ``tenant_id`` to determine if any agent has already handled a request for that tenant (i.e., has 'agent-tenant affinity').
#. If the scheduler finds an agent that has affinity with the loadbalancer's tenant, it selects that agent to complete the request.
#. If the scheduler doesn't find an agent that either is bound to the loadbalancer or has affinity with the loadbalancer's ``tenant_id``, it selects an active agent at random.

    * The selected agent is then bound to the loadbalancer and handles all future LBaaS requests associated with it.

#. If the agent bound to the loadbalancer is inactive, the scheduler looks for other active agents with tenant affinity and assigns the task to the first one it finds. The loadbalancer remains bound to the original agent, with the expectation that the agent will eventually come back online.

.. warning::

    If you delete an agent, you should also delete all loadbalancers bound to that agent.

    To view all loadbalancers associated with a specific agent:

    .. code-block:: bash

        $ neutron lbaas-loadbalancer-list-on-agent <agent-id>


Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.
- Operational OpenStack cloud (|openstack| release).
- Administrator access to both the BIG-IP device(s) and the OpenStack cloud.


Caveats
-------
- All hosts running F5 LBaaSv2 must use the same Neutron database.
- You **can not** run multiple agents on the same host if they are expected to manage the same BIG-IP device or cluster.
- See :ref:`Differentiated Service Environments` for information about running more than one F5 agent/driver on the same host.


Configuration
-------------

#. Copy the Neutron config file over to each host from which you want to run F5 LBaaSv2:

    .. code-block:: bash

        $ sudo cp /etc/neutron/neutron.conf <new_host>:/etc/neutron/neutron.conf

#. :ref:`Install the F5 Agent` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` on each host.

#. :ref:`Configure the F5 agent <Configure the F5 OpenStack Agent> on each host.

    .. tip::

        This can be as simple as configuring the file on one host and copying it over to the others.

#. :ref:`Start the agent <Starting the F5 agent>`.


Further Reading
---------------

.. seealso::

    * :ref:`Configure the F5 OpenStack Agent`
    * :ref:`Differentiated Service Environments`
    * :ref:`Manage BIG-IP Clusters with F5 LBaaSv2`
    * :ref:`Manage Multi-Tenant BIG-IP Devices with F5 LBaaSv2`
