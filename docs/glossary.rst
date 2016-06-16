Glossary
########

.. glossary::
    :sorted:

    device
        `BIG-IP®`_ hardware or virtual edition (VE).

    overcloud
        `BIG-IP®`_ virtual edition (VE) deployed as an OpenStack instance.

    undercloud
        `BIG-IP®`_ device (hardware or VE) deployed outside of OpenStack.

    standalone
        A single `BIG-IP®`_ device; no :term:`HA`.

    cluster
    clustered
    device cluster
    device service cluster
    device service clusters
    device service group
    DSC
    DSG
        Two (2) or more `BIG-IP®`_ devices configured to use :term:`high availability` features, providing synchronization and failover of BIG-IP configuration data among multiple BIG-IP devices on a network. A clustered BIG-IP device can synchronize some or all of its configuration data among several BIG-IP devices; fail over to one of many available devices; mirror connections to a peer device to prevent interruption in service during failover.

    high availability
    highly available
    HA
        The ability of a `BIG-IP®`_ device to process network traffic successfully. An HA device is generally part of a :term:`device cluster`.

    pair
        Two (2) `BIG-IP®`_ devices configured to use the :term:`active/standby` :term:`HA` mode.

    scalen
        Two (2) or more `BIG-IP®`_ devices configured as an active :term:`device cluster`.

    active/active
        Both `BIG-IP®`_ devices in a :term:`pair` are in an active state, processing traffic for different virtual servers or SNATs. If one device :term:`fails over`, the remaining device processes traffic from the failed device in addition to its own traffic.

    active/standby
    active-standby
        Only one of the two `BIG-IP®`_ devices is in an active state -- that is, processing traffic -- at any given time. If the active device :term:`fails over`, the second device enters active mode and processes traffic that was originally targeted for the primary device.

    failover
    fail over
    fails over
        Failover occurs when one device in an :term:`active/standby` pair becomes unavailable; the secondary device processes traffic that was originally targeted for the primary device.

    mirror
    mirroring
        A `BIG-IP®`_ system redundancy feature that ensures connection and persistence information is shared to another device in a device service cluster; mirroring helps prevent service interruptions if/when :term:`failover` occurs.

    SSL offloading
        SSL offloading relieves a Web server of the processing burden of encrypting and/or decrypting traffic sent via SSL, the security protocol that is implemented in every Web browser. For more information, see the `F5 Glossary <https://f5.com/glossary/ssl-offloading>`_.



.. _BIG-IP®: https://f5.com/products/big-ip