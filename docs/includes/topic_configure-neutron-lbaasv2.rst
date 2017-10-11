:orphan: true

.. _configure-neutron-lbaasv2:

Configure Neutron for LBaaSv2
=============================

You will need to make a few configurations in your Neutron environment in order to use the F5 OpenStack LBaasv2 driver and agent.

First, you'll need to set F5 Networks as the Neutron LBaaSv2 service provider driver. Then, add the LBaaSv2 plugin to the list of service plugins in the Neutron configuration file.

Set 'F5Networks' as the LBaaSv2 Service Provider
------------------------------------------------

Edit the ``service_providers`` section of :file:`/etc/neutron/neutron_lbaas.conf` as shown below to set 'F5Networks' as the LBaaSv2 service provider.

    .. code-block:: text
        :emphasize-lines: 4

        $ vi /etc/neutron/neutron_lbaas.conf
        ...
        [service_providers]
        service_provider = LOADBALANCERV2:F5Networks:neutron_lbaas.drivers.f5.driver_v2.F5LBaaSV2Driver:default
        ...

.. note::

    If there is an active entry for the F5 LBaaSv1 service provider driver, comment (#) it out.

Add the Neutron LBaaSv2 Service Plugin
--------------------------------------

Edit the ``[DEFAULT]`` section of the Neutron config file -- :file:`/etc/neutron/neutron.conf`.

1. Add the lbaasv2 service plugin as shown below.

    .. code-block:: text

        $ vi /etc/neutron/neutron.conf
        ...
        [DEFAULT]
        service_plugins = [already defined plugins],neutron_lbaas.services.loadbalancer.plugin.LoadBalancerPluginv2
        ...

2. Remove the entry for the LBaaSv1 service plugin (``lbaas``).

Restart Neutron
---------------

Use the command appropriate for your OS to restart the ``neutron-server`` service.

    .. code-block:: text

        $ sudo service neutron-server restart    \\ Ubuntu
        $ sudo systemctl restart neutron-server  \\ CentOS
