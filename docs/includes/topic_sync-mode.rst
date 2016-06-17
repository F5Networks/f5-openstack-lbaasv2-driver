:orphan: true

Sync mode
=========

Overview
--------

Sync mode refers to how the F5® agent syncs with the BIG-IP® device(s) it manages. The F5 agent uses sync mode to configure LBaaS objects on BIG-IP devices.

Use Case
--------

Sync mode applies specifically to environments using :term:`high availability`. The F5 agent uses ``replication`` mode to configure LBaaS objects on each device in a :term:`pair` or :term:`cluster` in real time (in other words, as objects are created in Neutron, they are synced to BIG-IP devices).

Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- Basic understanding of `BIG-IP® Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <install-f5-lbaasv2-driver>` installed on the Neutron controller and all other hosts for which you want to provision LBaaS services.


Caveats
-------
None.


Configuration
-------------
N/A; ``f5_sync_mode`` should not be changed from the default setting (``replication``).

Further Reading
---------------

.. seealso::

    * :ref:`HA mode`

