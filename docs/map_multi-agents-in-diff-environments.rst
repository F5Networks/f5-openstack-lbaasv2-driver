Multiple Agents and Differentiated Service Environments
=======================================================

Overview
--------

You can run :ref:`multiple F5 agents <Agent Redundancy and Scale Out>` on separate hosts in OpenStack to provide agent redundancy and scale out. Additionally, you can set up custom :ref:`service environments <Differentiated Service Environments>` in your OpenStack cloud to manage environments with different requirements and/or configurations.

Use Case
--------

In a typical multi-agent deployment, agents running on the same Neutron controller must be managing different BIG-IPs. In this case, when you request a new load balancer, you can not designate the BIG-IP on which the requested object will be created.

If you want to create LBaaS objects on specific BIG-IP(s) when using a multi-agent deployment, you'll need to run the agents in a custom :ref:`service environment <Differentiated Service Environments>`.

Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device service cluster`.
- Operational OpenStack cloud (|openstack| release).
- F5 ref:`agent <Install the F5 Agent>` and :ref:`LBaaSv2 driver <Install the F5 LBaaSv2 Driver>` installed on all hosts from which BIG-IP services will be provisioned.
- Basic understanding of `BIG-IP system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.
- Basic understanding of `BIG-IP Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

Caveats
-------

None.

Configuration
-------------

#. Generate a new custom environment on the Neutron controller.

    .. include:: includes/topic_differentiated-services.rst
        :start-after: command:
        :end-before: Configure the F5 Agent

#. :ref:`Configure the F5 agents <Configure the F5 OpenStack Agent>`.

    * Each agent must be configured with the same iControl endpoint(s).
    * Each agent must be configured with the same ``environment_prefix``; this is the name you assigned to the new custom environment.
    * Each agent must run on a separate host (in other words, the hostname must be unique).

#. Copy the Neutron and Neutron LBaaS configuration files from the Neutron controller to each host on which an agent is configured.

    .. code-block:: console

        $ sudo cp /etc/neutron/neutron.conf <openstack_host>:/etc/neutron/neutron.conf
        $ sudo cp /etc/neutron/neutron_lbaas.conf <openstack_host>:/etc/neutron/neutron_lbaas.conf

#. :ref:`Restart Neutron`.

#. :ref:`Start the F5 agent` on each host.


Usage
-----

When you create a new load balancer, you must specific the service provider driver to use; this is how F5 LBaaSv2 determines which queue should receive the task. The F5 LBaaSv2 driver responsible for that queue  then assigns the task to an agent as described in :ref:`Agent Redundancy and Scale Out`.

**Example:**

    .. code-block:: console

        (neutron) lbaas-loadbalancer-create --name lb_dev1 --provider dev1 b3fa44a0-3187-4a49-853a-24819bc24d3e
        Created a new loadbalancer:
        +---------------------+--------------------------------------+
        | Field               | Value                                |
        +---------------------+--------------------------------------+
        | admin_state_up      | True                                 |
        | description         |                                      |
        | id                  | fcd874ce-6dad-4aef-9e69-98d1590738cd |
        | listeners           |                                      |
        | name                | lb_dev1                              |
        | operating_status    | OFFLINE                              |
        | provider            | dev1                                 |
        | provisioning_status | PENDING_CREATE                       |
        | tenant_id           | 1b2b505dafbc487fb805c6c9de9459a7     |
        | vip_address         | 10.1.2.7                             |
        | vip_port_id         | 079eb9e5-dc63-4dbf-bc15-f38f5fdeee92 |
        | vip_subnet_id       | b3fa44a0-3187-4a49-853a-24819bc24d3e |
        +---------------------+--------------------------------------+




