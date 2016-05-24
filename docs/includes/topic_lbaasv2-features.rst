LBaaSv2 Features
----------------

The following configurable LBaaSv2 options are supported in release |release|. These options are set in the :ref:`F5® agent configuration file <agent:agent-configuration-file>` (:file:`/etc/neutron/services/f5/f5-openstack-agent.ini`). For configuration instructions and further details, please see the :ref:`F5® agent documentation <agent:configure-the-f5-openstack-agent>`.

Global Routed Mode
``````````````````

Setting ``f5_global_routed_mode`` to ``true`` causes the F5® agent to assume that all VIPs and pool members are reachable via global device L3 routes, which must be already provisioned on the BIG-IP®s. Set this option to ``false`` if you wish to use L2/L3 segmentation.

L2/L3 Segmentation Modes
````````````````````````

L2/L3 segmentation modes allow you to provision LBaaS services for BIG-IP® device(s) deployed outside of your OpenStack cloud.

- ``f5_external_physical_mappings``: Device VLAN to interface and tag mapping

    * ``physical_network`` corresponds to ``provider:physical_network`` attributes
    * ``interface_name`` is the name of an interface or LAG trunk
    * ``tagged`` is a boolean (True or False)


-  ``f5_vtep_folder``, ``f5_vtep_selfip_name``: Device Tunneling (VTEP) selfips

    The name of a folder and selfip address to use for VTEP addresses.

- ``advertised_tunnel_types``: Tunnel types

    A comma-separated list of tunnel types to report as available from the F5® agent, as well as to send via ``tunnel_sync`` rpc messages to compute nodes.

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


SSL Offloading
``````````````

- ``cert_manager``: The certificate manager that manages access to certificates and keys for user authentication. Must be set to ``f5_openstack_agent.lbaasv2.drivers.bigip.barbican_cert.BarbicanCertManager``.

- Keystone v2/v3 authentication

    - ``auth_version``: Keystone version (``v2`` or ``v3``)
    - ``os_auth_url``: Keystone authentication URL
    - ``os_username``: OpenStack username
    - ``os_password``: OpenStack password
    - ``os_tenant_name``: OpenStack tenant name (v2 only)
    - ``os_user_domain_name``: OpenStack domain in which the user account resides (v3 only)
    - ``os_project_name``: OpenStack project name (v3 only; refers to the same data as ``os_tenant_name`` in v2)
    - ``os_project_domain_name``: OpenStack domain in which the project resides



