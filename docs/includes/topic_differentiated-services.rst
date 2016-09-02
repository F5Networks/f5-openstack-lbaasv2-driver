:orphan: true

Differentiated Service Environments
===================================

Overview
--------

The F5® LBaaSv2 driver and F5 agent can manage multiple BIG-IP environments. In a :dfn:`differentiated service environment` -- a uniquely-named environment for which dedicated F5 LBaaS services are required -- the F5 driver  has its own, uniquely-named messaging queue. The F5 LBaaS agent scheduler for a differentiated service environment can only assign tasks to agents running in that environment.

The service environment corresponds to the ``environment_prefix`` parameter in the :ref:`agent configuration file`. when you create a new ``lbaas-loadbalancer`` in OpenStack, this prefix is prepended to the OpenStack tenant id and used to create a new partition on your BIG-IP® device(s). The default ``environment_prefix`` parameter is ``Project_``.

Differentiated service environments can be used in conjunction with :ref:`capacity-based scale out` to provide agent redundancy and scale out across BIG-IP device groups.

Neutron Service Provider Driver Entries
```````````````````````````````````````

The default service environment, ``Project_``, corresponds to the generic F5Networks :ref:`service provider driver <Set 'F5Networks' as the LBaaSv2 Service Provider>` entry in the Neutron LBaaS configuration file (:file:`/etc/neutron/neutron_lbaas.conf`).

.. important::

    Each unique service environment must have a corresponding service provider driver entry. You can use the :ref:`F5 environment generator` to easily create a new environment and configure Neutron to use it.

Use Case
--------

Differentiated service environments can be used to manage LBaaS objects for unique environments, which may have requirements that differ from those of other service environments.

Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device service cluster`.
- Operational OpenStack cloud (|openstack| release).
- F5 ref:`agent <Install the F5 Agent>` and :ref:`LBaaSv2 driver <Install the F5 LBaaSv2 Driver>` installed on all hosts from which BIG-IP services will be provisioned.
- Basic understanding of `BIG-IP system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.
- Basic understanding of `BIG-IP Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

Caveats
-------

- BIG-IP devices can not share anything across differentiated service environments. This precludes the use of vCMP, because vCMP guests share global VLAN IDs.


Configuration
-------------

Create a Service Provider Driver
````````````````````````````````

You can use the :ref:`F5 environment generator` to automatically generate, and configure Neutron to use, a new service provider driver for a custom environment.

#. On each Neutron controller which will host your custom environment, run the following command:

    .. code-block:: shell

        $ python -m f5lbaasdriver.utils.add_environment.py <provider_name> <environment_prefix>

#. Remove the comment (`#`) from the beginning of the new ``service_provider`` line to activate the driver.

.. topic:: Example: Create a custom environment called 'DEV1'.

    #. The python command:

        .. code-block:: shell

            $ python -m f5lbaasdriver.utils.add_environment.py DEV1 DEV1

    #. The corresponding ``service_provider`` entry added to :file:`/etc/neutron/neutron_lbaas.conf`.

        .. code-block:: text

            # service_provider = LOADBALANCERV2:DEV1:neutron_lbaas.drivers.f5.driver_v2_Dev1.F5LBaaSV2Driver:default

Configure the F5 Agent
``````````````````````

#. :ref:`Edit the agent configuration file`

#. Change the ``environment_prefix`` parameter to match the name of your custom environment.

#. :ref:`Restart Neutron`.

#. :ref:`Start the F5 agent`.



Further Reading
---------------

.. seealso::

    * :ref:`Configure the F5 OpenStack Agent`
    * :ref:`Configure Neutron for LBaaSv2`
    * :ref:`F5 Environment Generator`



