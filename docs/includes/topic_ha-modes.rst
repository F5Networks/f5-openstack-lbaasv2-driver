:orphan: true

HA mode
=======

Overview
--------

:term:`HA`, or, 'high availability', mode refers to high availability of the BIG-IP® device(s). The F5® agent can configure BIG-IP to operate in :term:`standalone`, :term:`pair`, or :term:`scalen` mode. The F5 agent uses :ref:`replication` to configure LBaaS objects on HA devices in real time.

Use Case
--------

High availability modes provide redundancy, helping to ensure service interruptions don't occur if a device goes down.

* :term:`standalone` mode utilizes a single BIG-IP device; here, 'high availability' means that BIG-IP core services are up and running, and VLANs are able to send and receive traffic to and from the device.

* :term:`pair` mode requires two (2) BIG-IP devices.

  BIG-IP pairs can operate in :term:`active/standby` or :term:`active/active` mode. Active/standby is the recommended mode for redundant system configuration. When an event occurs that prevents the 'active' BIG-IP device from processing network traffic, the 'standby' device immediately begins processing that traffic so users experience no interruption in service.

  In active/active mode, both devices in the pair are actively handling traffic. If an event occurs that prevents one device from porcessing traffic, traffic is automatically directed to the other active device in the pair.

* :term:`scalen` mode requires a :term:`device service cluster` of more than two (2) BIG-IP devices. Scalen allows you to configure multiple active devices which can fail over to any of many available standby devices.



Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device`, :term:`pair`, or :term:`device cluster`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- Basic understanding of OpenStack networking concepts. See the `OpenStack docs <http://docs.openstack.org/liberty/>`_ for more information.

- Basic understanding of `BIG-IP® Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <install-f5-lbaasv2-driver>` installed on the Neutron controller and all other hosts for which you want to provision LBaaS services.

- Two (2) VLANs :ref:`configured in Neutron <docs:os-neutron-network-setup>` to be used for BIG-IP internal and external traffic.


Caveats
-------

- If you only have one (1) BIG-IP deployed, you must use ``standalone`` mode.

- In this context, HA pertains to the BIG-IP device(s), not to the F5 agent itself.


Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini

2. Set the ``f5_ha_type`` as appropriate for your environment.

    - ``standalone``: single BIG-IP device
    - ``pair``: :term:`active/standby` or :term:`active/active` pair of BIG-IP devices
    - ``scalen``: BIG-IP :term:`device service cluster`

.. topic:: Example

    .. code-block:: text

        #
        # HA mode
        #
        # Device can be required to be:
        #
        # standalone - single device no HA
        # pair - active/standby two device HA
        # scalen - active device cluster
        #
        #
        f5_ha_type = standalone
        #



Further Reading
---------------

.. seealso::

    * `Introducing BIG-IP Device Service Clustering <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-device-service-clustering-admin-12-0-0/2.html?sr=55108154>`_

    * `Creating an active-standby DSC configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-implementations-12-0-0/5.html?sr=55107986>`_

    * `Creating an active-active DSC configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-implementations-12-0-0/6.html#conceptid>`_

    * `Configuring load-aware failover <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-implementations-12-0-0/7.html#conceptid>`_










