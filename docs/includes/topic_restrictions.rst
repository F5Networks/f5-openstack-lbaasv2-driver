Restrictions
------------

.. note::

    The features supported in |release| are a subset of the `Neutron LBaaSv2 API <https://wiki.openstack.org/wiki/Neutron/LBaaS/API_2.0>`_ delivered in the OpenStack Liberty release. The following restrictions apply:

    .. table::

        +----------------+----------------------------------------------------+
        | Object         | Unsupported                                        |
        +================+====================================================+
        | Listener       || ``TERMINATED_HTTPS``                              |
        |                || ``sni_container_refs``                            |
        |                || ``default_tls_container_ref``                     |
        +----------------+----------------------------------------------------+
        | Loadbalancer   || Statistics                                        |
        |                || (e.g., ``neutron lbaas-loadbalancer-stats``)      |
        |                || SSL (TLS protocol)                                |
        +----------------+----------------------------------------------------+

Unsupported Features
--------------------

The following features are unsupported in |release|; they will be introduced in future releases.

* vCMP® (multi-tenancy)
* Agent High Availability
* BIG-IP® Device Service Clustering
* Multiple environments (Prod, Dev, Test)
