:orphan: true

Overview
--------

The F5® OpenStack LBaaSv2 service provider driver and agent (also called the 'F5 LBaaSv2 plugin') make it possible to provision F5 BIG-IP® `Local Traffic Manager <https://f5.com/products/modules/local-traffic-manager>`_ (LTM®) services in an OpenStack cloud.

How the plugin works
````````````````````

The F5 LBaaSv2 plugin consists of an :ref:`agent <agent:home>` and a service provider driver (also just called 'driver', for short). The driver listens to the Neutron RPC messaging queue. When you make a call to the LBaaSv2 API -- for example, ``neutron lbaas-loadbalancer-create`` -- the F5 LBaaSv2 service provider driver picks it up and directs it to the agent.

The F5 agent manages services on your BIG-IP. When it first receives a task from the F5 driver, it starts and communicates with the BIG-IP(s) identified in the :ref:`agent configuration file`. Then, it registers its own named queue. The F5 driver assigns all ``lbaas`` tasks in the Neutron messaging queue to the agent's queue. The F5 agent makes callbacks to the F5® driver to query additional Neutron network, port, and subnet information; to allocate Neutron objects (for example, fixed IP addresses); and to report provisioning and pool status.

.. image:: http://f5-openstack-lbaasv1.readthedocs.io/en/liberty/_images/f5-lbaas-architecture.png
   :alt: F5 LBaaSv2 Plugin architecture


.. _start-neutron-port-note:

.. important::

   As of v8.3.1, the F5 LBaaSv2 driver no longer manages Neutron ports.

   When you create a pool member using the command ::

     neutron lbaas-member-create --subnet private-subnet --address 172.16.101.89 --protocol-port 80 pool1

   if the requested :code:`protocol-port` doesn't already exist on Neutron, you must create it manually.
   Previously, the F5 LBaaSv2 driver created a corresponding Neutron port for the member if it didn't exist.

   Likewise, if you create a pool member for which a corresponding Neutron port doesn't already exist, the F5 OpenStack Agent will not create a BIG-IP forwarding database (FBD) entry for the member.

.. _end-neutron-port-note: