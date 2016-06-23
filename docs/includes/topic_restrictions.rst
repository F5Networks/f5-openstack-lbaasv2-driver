.. _f5-agent-unsupported-features:

Unsupported Features
--------------------

The following F5® features are unsupported in |release|; they will be introduced in future releases.

* `BIG-IP® vCMP® <https://f5.com/resources/white-papers/virtual-clustered-multiprocessing-vcmp>`_
* Agent High Availability (HA)
* :ref:`Auto-sync mode <Sync mode>` for clustered devices
* Differentiated environments [#]_

The following OpenStack |openstack| `features <http://docs.openstack.org/releasenotes/neutron-lbaas/unreleased.html#new-features>`_ are unsupported in |release|:

* L7 Routing
* Unattached pools [#]_
* Loadbalancer statistics  (e.g., ``neutron lbaas-loadbalancer-stats``)


.. [#] Running multiple F5® agents on the same host to manage separate BIG-IP® environments.
.. [#] Creating a pool with no listener.
