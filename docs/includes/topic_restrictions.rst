:orphan: true

.. _f5-agent-unsupported-features:

Unsupported Features
--------------------

The following F5® features are unsupported in |release|; they will be introduced in future releases.

* `BIG-IP® vCMP® <https://f5.com/resources/white-papers/virtual-clustered-multiprocessing-vcmp>`_
* Agent High Availability (HA) [#]_
* Differentiated environments [#]_


.. note::

    The features supported in |release| are a subset of the `Neutron LBaaSv2 API <https://wiki.openstack.org/wiki/Neutron/LBaaS/API_2.0>`_ delivered in the OpenStack |openstack| release. The following restriction(s) apply:

    .. table::

        +----------------+----------------------------------------------------+
        | Object         | Unsupported                                        |
        +================+====================================================+
        | loadbalancer   || Statistics                                        |
        |                || (e.g., ``neutron lbaas-loadbalancer-stats``)      |
        +----------------+----------------------------------------------------+

* L7 Routing
* Unattached pools [#]_
* Loadbalancer statistics  (e.g., ``neutron lbaas-loadbalancer-stats``)

.. rubric:: Footnotes
.. [#] Similar to BIG-IP :term:`high availability`, but applies to the F5 agent processes.
.. [#] Multiple F5 agents running on the same host, managing *separate* BIG-IP environments.
.. [#] Creating a pool with no listener.



