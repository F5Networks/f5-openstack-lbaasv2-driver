.. _lbaasv2-driver-release-notes:

Release Notes |version|
#######################

.. rubric:: Summary

This release includes quality enhancements for the OpenStack Neutron LBaaSv2 service provider driver to support F5 Networks® BIG-IP® systems.

.. rubric:: Release Highlights

This release resolves API incompatibilities between agent and BIG-IP 11.5.4.

See the `changelog <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/compare/v8.0.4...v8.0.5>`_ for the full list of changes in this release.

.. rubric:: Caveats

The following are not supported in this release:

* BIG-IP vCMP
* Agent High Availability (HA)
* Differentiated environments
* L7 routing
* Unattached pools
* Loadbalancer statistics (e.g., ``neutron lbaas-loadbalancer-stats``)

.. rubric:: Open Issues

See the project `issues page <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/issues>`_ for a full list of open issues in this release.

