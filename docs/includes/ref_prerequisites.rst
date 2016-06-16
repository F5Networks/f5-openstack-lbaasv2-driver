.. INTERNAL USE ONLY
    The following prerequisites can be copied and pasted into any feature document.

- Licensed, operational BIG-IP :term:`device`.

- Operational OpenStack cloud (|openstack| release).

- F5 LBaaSv2 driver and :ref:`agent <agent:home>` installed on each server for which BIG-IP LTM services are required.

- `OpenStack Barbican`_ certificate manager configured and operational.

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- Licensed, operational BIG-IP :term:`device service cluster`.

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <install-f5-lbaasv2-driver>` installed on the Neutron controller and all other hosts for which you want to provision LBaaS services.

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.

- Login credentials for user with administrative permissions on BIG-IP device(s).


- Basic understanding of `BIG-IP® system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.


- Basic understanding of `BIG-IP® device service clustering <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html>`_.


- :ref:`SSH key(s) <heat:add-ssh-key-horizon>` configured in OpenStack.


- Two (2) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` -- 'mgmt' and 'data' - to be used for system management and data traffic, respectively.


- Three (3) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` -- 'mgmt', 'control', and 'data' -- to be used for system management, high availability (if desired), and data traffic, respectively.

- At least two (2) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` -- 'mgmt' and 'data' - to be used for BIG-IP® system management and client-server data traffic, respectively.

- An external network with access to the internet.


- Two (2) licensed, operational BIG-IP devices (hardware or Virtual Edition); both must be connected to the 'control' VLAN.

- BIG-IP `License base key <https://support.f5.com/kb/en-us/solutions/public/7000/700/sol7752.html>`_.

- Existing `BIG-IP® SSL profile`_ (*optional*).


.. _BIG-IP® SSL Profile: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-ssl-administration-12-0-0/5.html#unique_527799714