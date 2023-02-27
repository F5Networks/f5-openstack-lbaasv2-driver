.. index:: Release Notes

.. _Release Notes:

Release Notes
=============
v212.6.3 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2646] Multi-zone agent
* [OPENSTACK-2692] Always reload inventory file
* [OPENSTACK-2621] Change ACL functions for NG
* [OPENSTACK-2686] special scheduling to the new inactive device

Bug Fixes
`````````
* None noted

v212.6.2 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2608] Validate available SNAT IPs
* [OPENSTACK-2625] Bandwidth capacity filter
* [OPENSTACK-2596] Ensure device scheduling consistency
* [OPENSTACK-2596] Silently delete LB if no binding information
* [OPENSTACK-2596] Unify neutron constants name
* [OPENSTACK-2571] Refuse to create member with other tenant's subnet
* [OPENSTACK-2571] Optimize creating/deleting member performance

Bug Fixes
`````````
* None noted

v212.6.1 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2579] Subnet affinity filter
* [OPENSTACK-2560] Fix capacity filter failing to get flavor const
* [OPENSTACK-2560] Device capacity filter
* [OPENSTACK-2560] Device availability zone filter
* [OPENSTACK-2560] Device flavor filter
* [OPENSTACK-2560] Remove unlegacy_setting_placeholder_driver_side
* [OPENSTACK-2560] Remove "nova managed" agent case
* [OPENSTACK-2560] Get vtep ip from inventory instead of agent config
* [OPENSTACK-2560] Skip to compare network segment physical network
* [OPENSTACK-2560] Modify driver unit test
* [OPENSTACK-2532] Device scheduler
* [OPENSTACK-2560] Bump up version number
* [OPENSTACK-2532] Remove legacy bulk member code
* [OPENSTACK-2522] Enable driver to update port mac
* [OPENSTACK-2532] Skip loading loadbalancer in agent scheduler
* [OPENSTACK-2532] Remove legacy agent scheduler

Bug Fixes
`````````
* None noted

v212.5.8 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2512] Build service payload after update vip port
* [OPENSTACK-2490] Use network AZ hints if AZ is empty
* [OPENSTACK-2546] Use default AZ if either AZ or AZ hints is empty
* [OPENSTACK-2444] Support large SNAT pool

Bug Fixes
`````````
* None noted

Release Notes
=============
v212.5.7 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2512] Include VTEP IP address in Neutron port

Bug Fixes
`````````
* None noted

Release Notes
=============
v212.5.6 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2490] Schedule loadbalancer to desired availability zone

Bug Fixes
`````````
* None noted

Release Notes
=============
v212.5.5 (Pike)
--------------

Added Functionality
```````````````````
* [OPENSTACK-2479] Add get subnet rpc call

Bug Fixes
`````````
* None noted

Release Notes
=============
v212.5.4 (Pike)
--------------

Added Functionality
```````````````````
* feature: Add ACL function

Bug Fixes
`````````
* None noted

v212.5.3 (Pike)
--------------

Added Functionality
```````````````````
* add a new member batch operation rpc
* use the pool-id address and port to update the member

Bug Fixes
`````````
* Handle driver exception enhancement

v212.5.2 (Pike)
--------------

Added Functionality
```````````````````
* Compat with lb dict passed from neutron_lbaas.
* Pass persistence parameter to agent

Bug Fixes
`````````
* None noted.

v212.5.1 (Pike)
--------------

Added Functionality
```````````````````

Bug Fixes
`````````
* Fix loadbalancer not to stay pending_delete while loadbalancer creation error.


v212.5.0 (Pike)
--------------

Added Functionality
```````````````````
* Several performance improvements

Bug Fixes
`````````
* None noted.

v212.4.0 (Pike)
--------------

Added Functionality
```````````````````
* Add some time before and after db operation.

Bug Fixes
`````````
* Remove unexpected keyword argument.

v212.3.0 (Pike)
--------------

Added Functionality
```````````````````
* Add some logs.
* Some performance improvement.

Bug Fixes
`````````
* Route domain and partition deleted while deleting loadbalancer.


Limitations
```````````
* None noted.

v212.2.0 (Pike)
--------------

Added Functionality
```````````````````
* Members across net.
* Some performance improvement.


Bug Fixes
`````````
* None noted.


Limitations
```````````
* None noted.
