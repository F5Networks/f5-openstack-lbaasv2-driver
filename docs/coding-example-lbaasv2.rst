.. _coding-example-lbaasv2:

F5® OpenStack LBaaSv2 Plugin - Coding Example
=============================================

.. toctree::
    :hidden:
    :maxdepth: 1

We've provided some code examples below to help you get started with the F5® OpenStack LBaaSv2 plugin. This series demonstrates how to configure basic load balancing via the Neutron CLI.

To access the full Neutron LBaaS command set, please see the `OpenStack CLI Documentation <http://docs.openstack.org/cli-reference/neutron.html>`_. LBaaSv2 commands all begin with ``lbaas``.


Create a load balancer
``````````````````````
Use the command below to create a load balancer, specifying the load balancer name and its VIP subnet.

.. code-block:: shell

    $ neutron lbaas-loadbalancer-create --name lb1 private-subnet


Create a listener
`````````````````
Use the command below to create a listener for the load balancer specifying the listener name, load balancer name, protocol type, and protocol port.

.. code-block:: shell

    $ neutron lbaas-listener-create --name listener1 --loadbalancer lb1 --protocol HTTP --protocol-port 80


Create a pool
`````````````
Use the command below to create a pool for the listener specifiying the pool name, load balancing method, listener name, and protocol type.

.. code-block:: shell

    $ neutron lbaas-pool-create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP


Create a pool member
````````````````````
Use the command below to create a  member for the pool, specifying the subnet, IP address, and protocol port.

.. code-block:: shell

    $ neutron lbaas-member-create --subnet private-subnet --address 172.16.101.89 --protocol-port 80 pool1


Create a health monitor
```````````````````````
Use the command below to create a health monitor for the pool specifying the delay, monitor type, number of retries, timeout period, and pool name.

.. code-block:: shell

    $ neutron lbaas-healthmonitor-create --delay 3 --type HTTP --max-retries 3 --timeout 3 --pool pool1

