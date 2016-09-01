Multiple Controllers and Agent Redundancy
-----------------------------------------

The F5® LBaaSv2 plugin driver runs within the Neutron controller. When the Neutron community LBaaS plugin loads the
driver, it creates a global messaging queue that will be used for all inbound
callbacks and status update requests from F5® LBaaSv2 agents.

.. tip::

    To run multiple queues, see the :ref:`differentiated services <differentiated-services-scaleout>` section.

In an environment with multiple Neutron controllers, the F5® drivers all listen to the same
named message queue, providing controller redundancy and scale out. The drivers handle requests from the global queue in a round-robin fashion. All Neutron controllers must use the same Neutron database to avoid state problems with concurrently-running controller instances.

.. note::

    The agent service will expect to find an :file:`/etc/neutron/neutron.conf` file on its host; this file contains the configurations for Neutron messaging. To make sure the messaging settings match those of the controller, we recommend copying the :file:`/etc/neutron/neutron.conf` file from the controller to each additional host.

If you choose to deploy multiple agents with the same BIG-IP® ``environment_prefix``, each agent **must** run on a different host. Each agent will communicate with its configured iControl® endpoint(s) to do the following:

 * Verify that the BIG-IP® systems meet minimal requirements.
 * Create a specific named queue unique to itself for processing provisioning requests from service provider drivers.
 * Report as a valid F5® LBaaSv2 agent via the standard Neutron controller agent status queue.

The agents continue to report their status to the agent queue on a periodic basis (every 10 seconds, by
default; this can be configured in :file:`/etc/neutron/services/f5/f5-openstack-agent.ini`).

When a Neutron controller receives a request for a new loadbalancer, the F5® LBaaSv2 driver invokes the agent scheduler. The scheduler queries all active F5® agents and determines what, if any, existing loadbalancers are bound to each agent. If the driver locates an active agent that already has a bound loadbalancer for the same ``tenant_id`` as the newly-requested loadbalancer, the driver selects that agent. Otherwise, the driver selects an active agent at random. The request to create the loadbalancer service is sent to the selected agent's task queue. When the provisioning task is complete, the agent reports the outcome to the LBaaSv2 callback queue. The driver processes the agent's report and updates the Neutron database. The agent which handled the provisioning task is bound to the loadbalancer for the loadbalancer's lifetime (in other words, that agent will handle all tasks for that loadbalancer as long as the agent and/or loadbalancer are active). If a bound agent is inactive, the agent scheduler looks for other agents with the same ``environment_prefix`` as the bound agent. The scheduler assigns the task to the first active agent with a matching ``environment_prefix`` that it finds. The pool remains bound to the original (currently inactive) agent, with the expectation that the agent will eventually be brought back online.

.. warning::

     If you delete an agent, you should also delete all loadbalancers bound to that agent.

     Run ``neutron lbaas-loadbalancer-list-on-agent <agent-id>`` to identify all pools associated with an agent.
