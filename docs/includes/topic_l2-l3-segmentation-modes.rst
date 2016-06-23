:orphan: true

.. _l2-l3-segmentation-modes:

L2/L3 Segmentation Modes
========================

Overview
--------

The F5® agent L2/L3 segmentation mode settings tell the agent how the user's BIG-IP® device is configured.

.. warning::

    These settings must be configured correctly for the F5 agent to manage your BIG-IP(s). Knowledge of networking concepts and BIG-IP configuration is required.

.. rubric:: L2 segmentation mode settings include:

* Mapping VLANs to BIG-IP device interfaces (with or without tagging)
* Mapping VLAN tags to specific BIG-IP ports
* Device tunneling self IPs
* Tunnel types


.. rubric:: L3 segmentation mode settings include:

* :ref:`Global routed mode` / Route domains
* SNAT Mode and SNAT Address Counts
* Common Networks
* L3 Bindings

Use Case
--------

Typically, the F5 agent is used to manage one (1) or more :term:`undercloud` BIG-IP devices, deployed at the services layer of an external :ref:`provider network <docs:provider network>`. This allows users to apply existing BIG-IP services and configurations to resources in an OpenStack cloud. The flexibility of the L2/L3 segmentation mode settings make it possible to configure the agent to match your existing external network. Knowledge of the external network configuration, and that of the BIG-IP device(s) is required to configure these settings.


Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- Knowledge of `OpenStack Networking <http://docs.openstack.org/liberty/networking-guide/>`_ concepts.

- Knowledge of BIG-IP `system configuration`_, `local traffic management`_, & `device service clustering`_.

- VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` or `on the BIG-IP <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/5.html#conceptid>`_, as appropriate for your environment.

Caveats
-------

- Many L3 segmentation mode settings are dependent on how others are configured. It's important to read the text in the :ref:`agent configuration file` carefully before changing these settings to ensure they don't conflict.


Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini

2. Configure the L2 segmentation mode settings

    - ``f5_external_physical_mappings``: Maps VLANs to BIG-IP interfaces
    - ``vlan_binding_driver``: Binds tagged VLANs to specific BIG-IP ports; must be configured with a valid subclass of the iControl® :class:`VLANBindingBase` class. [#]_
    - ``f5_vtep_folder``: The name of the BIG-IP folder or partition in which the VTEP (virtual tunnel endpoint) resides; the default partition is 'Common'.
    - ``f5_vtep_selfip_name``: The name of the self IP assigned to the VTEP.
    - ``advertised_tunnel_types``: The type of tunnel(s) being used to access the BIG-IP device(s); can be comma-separated values if more than one tunnel type is being used.
    - ``f5_populate_static_arp``: Value must be True or False; indicates whether or not static arp entries are added for pool member IP addresses that are associated with VxLAN or GRE tunnel networks.
    - ``l2_population``: Value must be True or False; indicates whether BIG-IP will use L2 population service to update fbd tunnel entries.

.. topic:: Example: Device VLAN to interface and tag mapping

    .. code-block:: text
        :emphasize-lines: 31

        ###############################################################################
        #  L2 Segmentation Mode Settings
        ###############################################################################
        #
        # Device VLAN to interface and tag mapping
        #
        # For pools or VIPs created on networks with type VLAN we will map
        # the VLAN to a particular interface and state if the VLAN tagging
        # should be enforced by the external device or not.  This setting
        # is a comma separated list of the following format:
        #
        #    physical_network:interface_name:tagged, physical:interface_name:tagged
        #
        # where :
        #   physical_network corresponds to provider:physical_network attributes
        #   interface_name is the name of an interface or LAG trunk
        #   tagged is a boolean (True or False)
        #
        # If a network does not have a provider:physical_network attribute,
        # or the provider:physical_network attribute does not match in the
        # configured list, the 'default' physical_network setting will be
        # applied. At a minimum you must have a 'default' physical_network
        # setting.
        #
        # standalone example:
        #   f5_external_physical_mappings = default:1.1:True
        #
        # pair or scalen (1.1 and 1.2 are used for HA purposes):
        #   f5_external_physical_mappings = default:1.3:True
        #
        f5_external_physical_mappings = default:1.1:True
        #
        #
        # Device Tunneling (VTEP) selfips
        #
        # This is a single entry or comma separated list of cidr (h/m) format
        # selfip addresses, one per BIG-IP® device, to use for VTEP addresses.
        #
        # If no gre or vxlan tunneling is required, these settings should be
        # commented out or set to None.
        #
        f5_vtep_folder = None
        f5_vtep_selfip_name = None
        #
        #
        #
        # Tunnel types
        #
        # This is a comma separated list of tunnel types to report
        # as available from this agent as well as to send via tunnel_sync
        # rpc messages to compute nodes. This should match your ml2
        # network types on your compute nodes.
        #
        # If you are using only gre tunnels it should be:
        #
        # advertised_tunnel_types = gre
        #
        # If you are using only vxlan tunnels it should be:
        #
        advertised_tunnel_types = vxlan
        #
        # If this agent could get both gre and vxlan tunnel networks:
        #
        # advertised_tunnel_types = gre,vxlan
        #
        # If you are using only vlans only it should be:
        #
        # advertised_tunnel_types =
        #
        # Static ARP population for members on tunnel networks
        #
        # This is a boolean True or False value which specifies
        # that if a Pool Member IP address is associated with a gre
        # or vxlan tunnel network, in addition to a tunnel fdb
        # record being added, that a static arp entry will be created to
        # avoid the need to learn the member's MAC address via flooding.
        #
        # f5_populate_static_arp = True
        #
        # Device Tunneling (VTEP) selfips
        #
        # This is a boolean entry which determines if they BIG-IP® will use
        # L2 Population service to update its fdb tunnel entries. This needs
        # to be setup in accordance with the way the other tunnel agents are
        # setup.  If the BIG-IP® agent and other tunnel agents don't match
        # the tunnel setup will not work properly.
        #
        l2_population = True
        #



Further Reading
---------------

.. seealso::

    * :download:`Sample Agent Configuration file for GRE <../_static/f5-openstack-agent.gre.ini>`
    * :download:`Sample Agent Configuration file for VLAN <../_static/f5-openstack-agent.vlan.ini>`
    * :download:`Sample Agent Configuration file for VXLAN <../_static/f5-openstack-agent.vxlan.ini>`


L2/L3 Segmentation Modes
========================

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


.. rubric:: Footnotes
.. [#] Unsupported in v |release|


.. _system configuration: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid
.. _local traffic management: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html
.. _device service clustering: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html