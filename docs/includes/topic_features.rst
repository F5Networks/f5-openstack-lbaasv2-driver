LBaaSv2 Features
----------------

The configurable options supported in release |release| are noted below. See the agent configuration file -- :file:`/etc/neutron/services/f5/f5-openstack-agent.ini` -- for more information about each feature.


Global Routed Mode
``````````````````
Setting ``f5_global_routed_mode`` to ``true`` causes the agent to assume that all VIPs and pool members will be reachable via global device L3 routes, which must be already provisioned on the BIG-IP®s. Set this option to ``false`` if you wish to use L2/L3 segmentation.

    .. code-block:: text

        # Global Routing Mode - No L2 or L3 Segmentation on BIG-IP®
        #
        # This setting will cause the agent to assume that all VIPs
        # and pool members will be reachable via global device
        # L3 routes, which must be already provisioned on the BIG-IP®s.
        #
        # ...
        #
        f5_global_routed_mode = True
        #

L2/L3 Segmentation Modes
````````````````````````

L2/L3 segmentation modes allow you to provision LBaaS services for BIG-IP® device(s) deployed outside of your OpenStack cloud.

- ``f5_external_physical_mappings``: Device VLAN to interface and tag mapping

    Must use the following format:

    .. code-block:: text

        physical_network:interface_name:tagged

    * ``physical_network`` corresponds to ``provider:physical_network`` attributes
    * ``interface_name`` is the name of an interface or LAG trunk
    * ``tagged`` is a boolean (True or False)

    .. code-block:: text

        f5_external_physical_mappings = default:1.1:True

-  ``f5_vtep_folder``, ``f5_vtep_selfip_name``: Device Tunneling (VTEP) selfips

    The name of a folder and selfip address to use for VTEP addresses.

    .. code-block:: text

        # ...
        # If no gre or vxlan tunneling is required, these settings should be
        # commented out or set to None.
        #
        f5_vtep_folder = 'Common'
        f5_vtep_selfip_name = 'vtep'
        #

- ``advertised_tunnel_types``: Tunnel types

    A comma-separated list of tunnel types to report as available from the F5® agent, as well as to send via ``tunnel_sync`` rpc messages to compute nodes.

    .. code-block:: text

        # If you are using only gre tunnels it should be:
        #
        # advertised_tunnel_types = gre
        #
        # If you are using only vxlan tunnels it should be:
        #
        # advertised_tunnel_types = vxlan
        #
        # If this agent could get both gre and vxlan tunnel networks:
        #
        # advertised_tunnel_types = gre,vxlan
        #
        # If you are using only vlans only it should be:
        #
        # advertised_tunnel_types =
        #

HA model
````````

- ``f5_ha_type``: Defines the high availability mode used by the BIG-IP®.

    * ``standalone``: Single BIG-IP® device; no high availability.
    * ``pair`` and ``scalen``: not available in this release.

Sync mode
`````````

- ``f5_sync_mode``: Defines the model by which policies configured on one BIG-IP® are shared with other BIG-IP®s.

    * ``replication``: each device is configured separately.
    * ``autosync``: not available in this release (only ``standalone`` devices are currently supported).



