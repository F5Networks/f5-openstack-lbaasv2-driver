:orphan: true

.. INTERNAL USE ONLY
    The following prerequisites can be copied and pasted into any feature document.

- Licensed, operational BIG-IP :term:`device`.

- Licensed, operational BIG-IP :term:`device service cluster`.

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- Login credentials for user with administrative permissions on BIG-IP device(s).

- F5 :ref:`LBaaSv2 driver <Install the F5 LBaaSv2 Driver>` and :ref:`agent <agent:home>` installed on each server from which BIG-IP LTM services are required.

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` installed on the Neutron controller and all other hosts from which you want to provision LBaaS services.

- Basic understanding of OpenStack networking concepts. See the `OpenStack docs <http://docs.openstack.org/liberty/>`_ for more information.


- Basic understanding of `BIG-IP® system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.

- Basic understanding of `BIG-IP® Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

- Basic understanding of `BIG-IP® device service clustering <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html>`_.

- Knowledge of `OpenStack Networking <http://docs.openstack.org/liberty/networking-guide/>`_ concepts.

- Knowledge of BIG-IP `system configuration`_, `local traffic management`_, & `device service clustering`_.
.. must include the following at end of document:
    .. _system configuration: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid
    .. _local traffic management: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html
    .. _device service clustering: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0.html

- :ref:`SSH key(s) <heat:add-ssh-key-horizon>` configured in OpenStack.

- Two (2) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` -- 'mgmt' and 'data' - to be used for system management and data traffic, respectively.

- Two (2) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` to be used for BIG-IP internal and external traffic.

- Three (3) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` -- 'mgmt', 'control', and 'data' -- to be used for system management, high availability (if desired), and data traffic, respectively.

- At least two (2) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` -- 'mgmt' and 'data' - to be used for BIG-IP® system management and client-server data traffic, respectively.

- VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` or `on the BIG-IP <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/5.html#conceptid>`_, as appropriate for your environment.

- An external network with access to the internet.

- Two (2) licensed, operational BIG-IP devices (hardware or Virtual Edition); both must be connected to the 'control' VLAN.

- BIG-IP `License base key <https://support.f5.com/kb/en-us/solutions/public/7000/700/sol7752.html>`_.

- `OpenStack Barbican <OpenStack Barbican: https://wiki.openstack.org/wiki/Barbican>`_ certificate manager configured and operational.

- Existing `BIG-IP® SSL profile <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-ssl-administration-12-0-0/5.html#unique_527799714>`_ (*optional*).

