.. _l2-l3-segmentation-modes:

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

    The name of a folder (partition) and self IP address from the BIG-IP® to use for VTEP addresses. 'Common' is the default partition on BIG-IP®.

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
