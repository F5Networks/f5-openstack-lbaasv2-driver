Configure the F5® OpenStack Agent
---------------------------------

Edit the agent configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit :file:`/etc/neutron/services/f5/f5-openstack-agent.ini` as appropriate for your environment. The configurations listed here are supported in |release|. See the :ref:`Release Notes <release-notes>` or the config file for more information about these features.

Device Settings
^^^^^^^^^^^^^^^

    .. code-block:: text

        # HA model
        #
        # ...
        #
        f5_ha_type = standalone
        #
        #
        # Sync mode
        #
        # ...
        #
        f5_sync_mode = replication
        #

L2/L3 Segmentation Mode Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    .. code-block:: text

        # Device VLAN to interface and tag mapping
        #
        # ...
        #
        f5_external_physical_mappings = default:1.1:True
        #

    .. code-block:: text

        # Device Tunneling (VTEP) selfips
        #
        # ...
        #
        f5_vtep_folder = 'Common'
        f5_vtep_selfip_name = '<name of a vtep selfip>'
        #
        #

    .. code-block:: text

        # Tunnel types
        #
        # ...
        #
        advertised_tunnel_types = 'gre' // Change to 'vxlan' if using vxlan tunnels
        #
        #

Global Routed Mode Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    .. code-block:: text

        # Global Routed Mode - No L2 or L3 Segmentation on BIG-IP®
        #
        # This setting will cause the agent to assume that all VIPs
        # and pool members will be reachable via global device
        # L3 routes, which must be already provisioned on the BIG-IP®s.
        #
        f5_global_routed_mode = True
        #

Device Driver - iControl® Driver Setting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    .. code-block:: text

        #
        icontrol_hostname = 10.190.6.105 \\ replace with the IP address of your BIG-IP®
        #
        # ...
        #
        # icontrol_username must be a valid Administrator username
        # on all devices in a device sync failover group.
        #
        icontrol_username = admin
        #
        # icontrol_password must be a valid Administrator password
        # on all devices in a device sync failover group.
        #
        icontrol_password = admin
        #

Start the F5® agent
~~~~~~~~~~~~~~~~~~~

Use the command(s) appropriate for your OS to start the agent.

    .. code-block:: text

        $ sudo service f5-oslbaasv2-agent start             \\ Debian/Ubuntu

        $ sudo systemctl enable f5-openstack-agent           \\ RedHat/CentOS
        $ sudo systemctl start f5-openstack-agent


