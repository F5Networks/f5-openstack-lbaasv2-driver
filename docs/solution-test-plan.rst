Solution Test Plan
==================

Introduction
------------

About this document
```````````````````

This document outlines the process for validating an Openstack deployment utilizing F5 products to provide Neutron LBaaSv2 (load balancing) services. Use cases are defined, for testing purposes, that encompass the set of standard F5 OpenStack solution deployments.

F5 OpenStack Integrated Solutions
`````````````````````````````````

F5 produces integration solutions that orchestrate BIG-IP Application Delivery Controllers (ADC) with OpenStack Networking (Neutron) services. F5 OpenStack LBaaSv2 integration provides under-the-cloud multi-tenant infrastructure L4-L7 services for Neutron tenants.

In addition to community OpenStack participation, F5 maintains partnerships with several OpenStack platform vendors. Each vendor defines a certification process, including test requirements, that expand on or focus tests available in community OpenStack. This document presumes use of a certified deployment; to the extent vendor tests have been or will be run to prove the validity of the deployment.

Community OpenStack and platform vendor tests exercise the generic LBaaSv2 integration. F5 OpenStack tests exercise F5-specific capabilities across multiple network topologies. They are complementary to community and platform vendor tests.

All F5 OpenStack tests are available in the same open source repository as the product code. They may be executed via tempest and tox, consistent with the OpenStack community, to allow self-validation of a deployment.

Use cases are based on real-world scenarios that represent repeatable deployments of the most common features used in F5 OpenStack integrations. Use case tests validate the combination of OpenStack, F5 BIG-IP ADC and F5 OpenStack products.

Prerequisites
-------------

OpenStack
`````````

* Operational OpenStack |openstack| cloud deployed in accordance with minimal documented requirements:

  * Deployment configuration will be varied to match test architectures described within each use case;
  * 1 host machine for a Controller node;
  * 1 host machine for a Compute node.

* Nova :ref:`flavor <docs:big-ip_flavors>`.

TMOS
````

* Supported TMOS :ref:`version <docs:F5 OpenStack Releases and Support Matrix>`.
* For Virtual Edition:

  * LTM_1SLOT KVM qcow2 image built using the supported Onboarding Heat :ref:`template <heat:F5 BIG-IP VE: Image Patch & Upload>`;
  * Instance deployed using the supported 3-NIC Heat :ref:`template <heat:F5 BIG-IP VE: Standalone, 3-nic>`.

* Operational BIG-IP :term:`device` or :term:`device service cluster` licensed with LTM and SDN Services.
* Initial configuration orchestrated to match the deployment architecture per the F5 LBaaSv2 Installation Guide.

F5 OpenStack LBaaSv2
````````````````````

* F5 :ref:`agent <Install the F5 Agent>` and :ref:`LBaaSv2 driver <Install the F5 LBaaSv2 Driver>` installed on all hosts from which BIG-IP services will be provisioned.
* Agent configuration will be varied to match test architectures described within each use case.

Test Plan
---------

Community OpenStack tests (not required, but recommended) are available to exercise the following key components:

* OpenStack Neutron for network topology deployment;
* OpenStack Nova for test web application deployment;
* OpenStack Neutron for LBaaSv2 service deployment:

  * `Instructions <http://docs.openstack.org/developer/tempest/overview.html>`_ for executing Tempest tests;
  * Tests compatible with F5 OpenStack LBaaSv2 are located in the community |community_tempest_lbaasv2_tests| repository.

F5 OpenStack tests (required) are available to exercise the following key components:

* F5 OpenStack LBaaSv2 plugin driver (|f5_lbaasv2_driver_readme|);
* F5 OpenStack Agent (|f5_agent_readme|).

Each use case requires execution of tests over one or more standard network deployments:

Network Architectures
`````````````````````

NA1: Global Routed Mode
~~~~~~~~~~~~~~~~~~~~~~~

Edge deployment architecture using only OpenStack networking provider networks, with F5 OpenStack agents deployed in :ref:`Global Routed Mode <global-routed-mode>`.

.. figure:: ../media/f5-lbaas-test-architecture-grm.png
    :align: center
    :alt: Global Routed Mode

NA2: L2 Adjacent Mode
~~~~~~~~~~~~~~~~~~~~~

Micro-segmentation architecture using tenant networks, with F5 agents deployed in :ref:`L2 Adjacent Mode <L2 Segmentation Mode>`. Execute tests for VLAN and then VxLAN network types.

.. figure:: ../media/f5-lbaas-test-architecture-l2adj.png
    :align: center
    :alt: L2 Adjacent Mode

F5 OpenStack tests supplement the community tests and exercise :ref:`features <Supported Features>` specific to F5.

Use Cases
`````````

UC1: Community LBaaSv2
~~~~~~~~~~~~~~~~~~~~~~

This use case focuses on basic integration of BIG-IP LTM to provide services through the OpenStack LBaaSv2 API. LBaaSv2 features tested include load balancers, listeners, pools, members, and monitors. LTM features tested include virtual servers, client TLS decryption, http profiles, multiple pools, cookie persistence, and monitored pool members. Pool member state and virtual server statistics are collected through OpenStack networking APIs.

.. table:: Use Case 1 Requirements

    +---------------+-------------------------------+
    | Category      | Requirements                  |
    +---------------+-------------------------------+
    | Architectures | 1, 2                          |
    +---------------+-------------------------------+
    | Tests         | | neutron-lbaas               |
    |               | | f5-openstack-lbaasv2-driver |
    +---------------+-------------------------------+

