.. _lbaas-env-generator:

F5 Environment Generator
========================

The F5 environment generator is a Python utility.
It creates a new service provider driver and adds it to the Neutron LBaaS configuration file (:file:`/etc/neutron/neutron_lbaas.conf`).

You can use the F5 environment generator with `Differentiated Service Environments`_ and `Capacity-based Scale out`_.

Usage
-----

To create a new service environment, run the command below on your Neutron controller.

.. code-block:: console

   add_f5agent_environment <env_name>

.. tip::

   The environment name must be eight (8) characters or less.


Next Steps
----------

You can use your new service environment to run multiple |agent| instances on the same host.
See the `Differentiated Service Environments`_ documentation for more information.

See `Capacity-Based Scale Out`_ to learn about agent redundancy and scale out for differentiated service environments.

