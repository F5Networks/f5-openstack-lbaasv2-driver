.. _lbaasv2-driver-release-notes:

Release Notes v |version|
#########################

Summary
-------

This release provides an implementation of the F5® service provider driver to support the use of F5 Networks® BIG-IP® systems with OpenStack Neutron LBaaSv2.

Release Highlights
------------------

This release introduces the following:

- Hierarchical port binding
- Bug fixes

See the `changelog <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/compare/v9.0.2...v9.0.3>`_ for the full list of changes in this release.

Caveats
-------

The following are not supported in this release:

* BIG-IP vCMP
* Agent High Availability (HA)
* Differentiated environments
* L7 routing
* Unattached pools
* Loadbalancer statistics (e.g., ``neutron lbaas-loadbalancer-stats``)

Open Issues
-----------

See the project `issues page <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/issues>`_ for a full list of open issues in this release.

