:orphan: true

.. _global-routed-mode:

Global Routed Mode
==================

Overview
--------

In global routed mode, the F5® agent assumes that LBaaS objects are accessible via global L3 routes. All virtual IPs are assumed routable from clients and all members are assumed routable from BIG-IP®. Virtual IPs are allocated from the OpenStack subnet identified in the ``neutron lbaas-create`` command.


.. need to verify whether the following should be included; talk to J Gruber and J Longstaff.
All L2 and L3 objects, including routes, must be provisioned on the BIG-IP before creating LBaaS objects in Neutron.
Global routed mode uses BIG-IP `secure network address translation`_ (SNAT) 'automapping', which allows you to map one or more origin IP addresses to a pool of translation addresses. The pool is created by the BIG-IP Local Traffic Manager® (LTM) from existing `self IP`_ addresses.
Before you configure the F5 agent to use global routed mode, you should create at least one VLAN on your BIG-IP, and create enough `self IP`_ addresses  to handle anticipated connection loads. [#]_ You do not need to configure a SNAT pool, as one will be created automatically.

Use Case
--------

Global routed mode is generally used for :term:`overcloud`, :term:`one-arm` BIG-IP VE deployments. It can be used for `client-initiated (inbound) connections`_ or `server-initiated (outbound) connections`_.

Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- F5 :ref:`LBaaSv2 driver <install-f5-lbaasv2-driver>` and :ref:`agent <agent:home>` installed on each server for which BIG-IP LTM services are required.

.. A group of `self IP`_ addresses must be provisioned on the BIG-IP **before** you provision LBaaS services.


Caveats
-------

- Global routed mode cannot be used with an :term:`undercloud` BIG-IP.

- In global routed mode, the underlying assumption is that all VIP L3 addresses are globally routable; this means that VLAN segmentation is not supported. Setting this mode to ``True`` means that all VIPs listen on all VLANs accessible to the BIG-IP.

- Because only one global routing space is used on the BIG-IP, overlapping IP addresses between tenants is not supported.

- All L3 routes must be set up on the BIG-IP before you provision LBaaS services.

- Using ``f5_common_external_networks`` is not supported for use with global routed mode; rather, it is assumed that all networks are configured within your OpenStack cloud, not on the BIG-IP.


Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini

2. Configure ``global_routed_mode`` and its dependent features.

    - ``global_routed_mode``: When set to ``True``, causes the agent to assume that all VIPs and pool members are reachable via global device L3 routes
    - ``use_namespaces``: Forced to ``False``; use of overlapping namespaces is not supported in global routed mode.
    - ``f5_snat_mode``: Forced to ``True``; forces the use of automap SNATs to allocate `self IP`_ addresses to LBaaS objects.
    - ``f5_snat_addresses_per_subnet``: Forced to ``0``; the device's local `self IP`_ is used to SNAT traffic.
    - ``f5_common_external_networks``: Set this to ``False``; this setting corresponds to networks configured on the BIG-IP that are not configured in OpenStack; global routed mode assumes all networks are configured within OpenStack.

.. topic:: Example

    .. code-block:: text
        :emphasize-lines: 13, 22, 46, 61

        ###############################################################################
        #  L3 Segmentation Mode Settings
        ###############################################################################
        #
        # Global Routed Mode - No L2 or L3 Segmentation on BIG-IP®
        #
        # This setting will cause the agent to assume that all VIPs
        # and pool members will be reachable via global device
        # L3 routes, which must be already provisioned on the BIG-IP®s.
        #
        ...
        #
        f5_global_routed_mode = True
        #
        # Allow overlapping IP subnets across multiple tenants.
        # This creates route domains on BIG-IP® in order to
        # separate the tenant networks.
        #
        # This setting is forced to False if
        # f5_global_routed_mode = True.
        #
        use_namespaces = False
        #
        ...
        #
        ...
        #
        # SNAT Mode and SNAT Address Counts
        #
        # This setting will force the use of SNATs.
        #
        # If this is set to False, a SNAT will not
        # be created (routed mode) and the BIG-IP®
        # will attempt to set up a floating self IP
        # as the subnet's default gateway address.
        # and a wild card IP forwarding virtual
        # server will be set up on member's network.
        # Setting this to False will mean Neutron
        # floating self IPs will no longer work
        # if the same BIG-IP® device is not being used
        # as the Neutron Router implementation.
        #
        # This setting will be forced to True if
        # f5_global_routed_mode = True.
        #
        f5_snat_mode = True
        #
        # This setting will specify the number of snat
        # addresses to put in a snat pool for each
        # subnet associated with a created local Self IP.
        #
        # Setting to 0 (zero) will set VIPs to AutoMap
        # SNAT and the device's local Self IP will
        # be used to SNAT traffic.
        #
        ...
        #
        # This setting will be forced to 0 (zero) if
        # f5_global_routed_mode = True.
        #
        f5_snat_addresses_per_subnet = 0
        #


3. Set ``f5_common_external_networks`` to ``False``.

.. topic:: Example

    .. code-block:: text
        :emphasize-lines: 5

        # This setting will cause all networks with
        # the router:external attribute set to True
        # to be created in the Common partition and
        # placed in route domain 0.
        f5_common_external_networks = False
        #


Further Reading
---------------

.. seealso::

    * :download:`Sample Agent Configuration file for Global Routed Mode <../_static/f5-openstack-agent.grm.ini>`

    * `TMOS Routing Overview <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/2.html#conceptid>`_

    * `BIG-IP AutoMap SNAT <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/8.html#unique_1573359865>`_


.. rubric:: Footnotes
.. [#] The VLAN(s) on the BIG-IP should correspond to the network(s) configured in your OpenStack cloud.


.. _secure network address translation: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/8.html#unique_427846607
.. _self IP: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/6.html#conceptid
.. _client-initiated (inbound) connections: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/8.html#unique_847331455
.. _server-initiated (outbound) connections: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/8.html#unique_1804816887

