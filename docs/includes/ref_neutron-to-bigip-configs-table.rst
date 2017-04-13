:orphan: true

Neutron Command to BIG-IP Configuration Mapping Table
=====================================================

F5 LBaaSv2 uses the `f5-sdk <http://f5-sdk.readthedocs.io/en/latest/>`_ to communicate with BIG-IP via the iControl REST API. The table below shows the corresponding iControl endpoint and BIG-IP object for each neutron lbaas- ‘create’ command.

+----------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------+
| Command                                | URI                                                                                     | BIG-IP Configurations Applied     |
+========================================+=========================================================================================+===================================+
| ``neutron lbaas-loadbalancer-create``  | \https://<icontrol_endpoint>:443/mgmt/tm/sys/folder/~Project_<os_tenant_id>             | new partition created using the   |
|                                        |                                                                                         | uuid prefix and tenant ID         |
+----------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------+
| ``neutron lbaas-listener-create``      | \https://<icontrol_endpoint>:443/mgmt/tm/ltm/virtual/                                   | new virtual server created in the |
|                                        |                                                                                         | tenant partition                  |
+----------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------+
| ``neutron lbaas-pool-create``          | \https://<icontrol_endpoint>:443/mgmt/tm/ltm/pool/                                      | new pool created on the virtual   |
|                                        |                                                                                         | server                            |
+----------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------+
| ``neutron lbaas-member-create``        | \https://<icontrol_endpoint>:443/mgmt/tm/ltm/pool/~Project_<os_tenant_id>~pool1/members/| new member created in the pool    |
+----------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------+
| ``neutron lbaas-healthmonitor-create`` | \https://<icontrol_endpoint>:443/mgmt/tm/ltm/monitor/http/                              | new health monitor created for    |
|                                        |                                                                                         | the pool                          |
+----------------------------------------+-----------------------------------------------------------------------------------------+-----------------------------------+




.. rubric:: Footnotes:
.. [#] The default prefix is "Project\_".


.. .. csv-table:: Neutron to BIG-IP Configuration Mapping
    :header: Command, Arguments, URI, BIG-IP Configurations Applied
    :widths: 10, 10, 10, 20
    ``neutron lbaas-loadbalancer-create``, ``--name`` <subnet_ID>,\https://<icontrol_endpoint>:443/mgmt/tm/sys/folder/~Project_<os_tenant_id>, new partition created
    ``neutron lbaas-listener-create``, ``--name`` <listener-name> ``--loadbalancer`` <loadbalancer-name> ``--protocol`` <example:HTTP> ``--protocol-port`` <example:80>, \https://<icontrol_endpoint>:443/mgmt/tm/ltm/virtual/, new virtual server created in the tenant partition
    ``neutron lbaas-pool-create``, ``--name`` <pool-name> ``--lb-algorithm`` <example:ROUND ROBIN> ``--listener`` <listener-name> ``--protocol`` <example: HTTP>, \https://10.190.3.55:443/mgmt/tm/ltm/pool/, new pool is created for the identified virtual server (listener)
    ``neutron lbaas-member-create``, ``--subnet`` <subnet_ID> ``--address`` <IP-address-in-subnet ``--protocol-port`` <example:80> <pool-name>, \https://10.190.3.55:443/mgmt/tm/ltm/pool/~Project_9572afc14db14c8a806d8c8219446e7b~pool1/members/, new member created with the identified parameters







