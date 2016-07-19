:orphan: true

F5 LBaaSv2 Configuration Options
================================


+----------------------------+--------------------+-------------------------------------------+
| Setting                    | Recommended Value  | | Description                             |
+============================+====================+===========================================+
| f5_global_routed_mode      | FALSE              | | If you use VxLAN tenant networks with   |
|                            |                    | | dynamically configured subnets,         |
|                            |                    | | global routed mode must be set to       |
|                            |                    | | FALSE.                                  |
|                            |                    | | This setting is also referred to as     |
|                            |                    | | L2-adjacent mode.                       |
|                            |                    | | When global routed mode is set to TRUE, |
|                            |                    | | the F5 agent does not attempt to manage |
|                            |                    | | any L2 or L3 network settings on the    |
|                            |                    | | BIG-IP dynamically. In this mode all    |
|                            |                    | | guest VMs are considered globally       |
|                            |                    | | routable and AutoMap SNAT is applied to |
|                            |                    | | all virtual servers on the BIG-IP.      |
+----------------------------+--------------------+-------------------------------------------+
| f5_vtep_folder             | Common             | | The BIG-IP partition/folder where the   |
|                            |                    | | preconfigured VTEP non-floating         |
|                            |                    | | SelfIP will be created.                 |
+----------------------------+--------------------+-------------------------------------------+
| f5_vtep_selfip_name        | vtep               | | The name of the preconfigured           |
|                            |                    | | non-floating SelfIP which will function |
|                            |                    | | as the VTEP for the BIG-IP. This        |
|                            |                    | | address has to be able to route to the  |
|                            |                    | | underlay network VTEP addresses of the  |
|                            |                    | | compute and network nodes               |
|                            |                    | | (``local_ips`` in the OpenStack OVS     |
|                            |                    | | configuration files).                   |
+----------------------------+--------------------+-------------------------------------------+
| advertised_tunnel_types    | vxlan              | | The agent will advertise the ability    |
|                            |                    | | to terminate these tunnel types through |
|                            |                    | | the ``tunnel_sync`` oslo message        |
|                            |                    | | queues. This should match your agent's  |
|                            |                    | | settings on the compute and network     |
|                            |                    | | nodes. The agent will register the      |
|                            |                    | | BIG-IPs as tunnel peers based on this   |
|                            |                    | | setting.                                |
+----------------------------+--------------------+-------------------------------------------+
| f5_populate_static_arp     | TRUE               | | When set to TRUE, the agent populates   |
|                            |                    | | the BIG-IP's ARP table with the IP and  |
|                            |                    | | MAC information from the LBaaS service  |
|                            |                    | | definition. This reduces the amount of  |
|                            |                    | | flood learning required to discover     |
|                            |                    | | pool members for the BIG-IP.            |
+----------------------------+--------------------+-------------------------------------------+
| l2_population              | TRUE               | | When set to TRUE, the agent registers   |
|                            |                    | | for ML2 L2 population messages, which   |
|                            |                    | | update the VTEP forwarding table when   |
|                            |                    | | pool members are migrated from one      |
|                            |                    | | compute node to another.                |
+----------------------------+--------------------+-------------------------------------------+
| use_namespaces             | TRUE               | | Each tenant should be assigned one or   |
|                            |                    | | more route domains on the BIG-IP. This  |
|                            |                    | | allows dynamically configured IP        |
|                            |                    | | subnets to overlap without causing L3   |
|                            |                    | | forwarding issues in the BIG-IP.        |
+----------------------------+--------------------+-------------------------------------------+
| f5_route_domain_strictness | FALSE              | | While each tenant will be assigned its  |
|                            |                    | | own route domain(s), provider networks  |
|                            |                    | | with external routes should be          |
|                            |                    | | accessible through the proxy. This      |
|                            |                    | | requires route domain strictness to be  |
|                            |                    | | set to FALSE, thus allowing the global  |
|                            |                    | | routing table on the BIG-IP to be       |
|                            |                    | | referenced if no matching destination   |
|                            |                    | | routes for tenant traffic is discovered |
|                            |                    | | within the tenant route domain.         |
+----------------------------+--------------------+-------------------------------------------+
| f5_snat_mode               | TRUE               | | The agent should manage a SNAT          |
|                            |                    | | translation address pool on behalf of   |
|                            |                    | | the tenant. Proxy traffic heading       |
|                            |                    | | towards the pool members will use a     |
|                            |                    | | SNAT translation address from this      |
|                            |                    | | pool, as the BIG-IP will not be         |
|                            |                    | | assuming the subnet default gateway     |
|                            |                    | | address.                                |
+----------------------------+--------------------+-------------------------------------------+
| f5_common_external_networks| TRUE               | | The agent places all provider           |
|                            |                    | | networks with the ``route:external``    |
|                            |                    | | attribute set to true (i.e., an         |
|                            |                    | | infrastructure router) and all          |
|                            |                    | | associated IP objects in the global     |
|                            |                    | | routing table (creates infrastructure-  |
|                            |                    | | based, not tenant-based, routes).       |
+----------------------------+--------------------+-------------------------------------------+
| cert_manager               | commented out/ None| | Commenting out this line, or setting    |
|                            |                    | | it to None, disables SSL offload        |
|                            |                    | | support so the F5 agent does not        |
|                            |                    | | attempt to communicate with the         |
|                            |                    | | Barbican service.                       |
|                            |                    |                                           |
|                            |                    | | If you have Barbican configured and     |
|                            |                    | | want to use SSL offloading, uncomment   |
|                            |                    | | this line and configure the             |
|                            |                    | | authentication settings as appropriate  |
|                            |                    | | for your environment.                   |
+----------------------------+--------------------+-------------------------------------------+
| - auth_version             | commented out      | | If you are using Barbican, uncomment    |
| - os_auth_url              |                    | | these lines and provide the             |
| - os_username              |                    | | appropriate information for your        |
| - os_password              |                    | | environment.                            |
| - os_user_domain_name      |                    |                                           |
| - os_project_name          |                    |                                           |
| - os_project_domain_name   |                    |                                           |
+----------------------------+--------------------+-------------------------------------------+
| icontrol_hostname          | | Comma separated  | | This is how the agent knows what        |
|                            | | list of BIG-IP   | | BIG-IP(s) to manage.                    |
|                            | | hostnames/       |                                           |
|                            | | IP addresses     |                                           |
+----------------------------+--------------------+-------------------------------------------+
| icontrol_username          | | BIG-IP admin     | | Used to manage the BIG-IP(s). This      |
|                            | | username         | | must be an account with Administrator   |
|                            |                    | | role as the agent will create global    |
|                            |                    | | objects in the BIG-IP configuration.    |
+----------------------------+--------------------+-------------------------------------------+
| icontrol_password          | | BIG-IP admin     | | Used to manage the BIG-IP(s). This      |
|                            | | password         | | must be an account with Administrator   |
|                            |                    | | role as the agent will create global    |
|                            |                    | | objects in the BIG-IP configuration.    |
+----------------------------+--------------------+-------------------------------------------+














