Glossary
########

.. glossary::
    :sorted:

    segmentation ID
    segmentation id
        `VLAN tag <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/tmos-routing-administration-12-0-0/5.html#unique_1525090453>`_

    device
        `BIG-IP`_ hardware or virtual edition (VE).

    overcloud
        `BIG-IP`_ virtual edition (VE) deployed as an OpenStack instance.

    undercloud
        `BIG-IP`_ device (hardware or VE) deployed outside of OpenStack.

    standalone
        A single `BIG-IP`_ device; no :term:`HA`.

    cluster
    clustered
    clustering
    device cluster
    device service cluster
    device service clusters
    DSC
        Device Service Clustering provides synchronization and failover of `BIG-IP`_ configuration data among multiple `BIG-IP`_ devices on a network. You can configure a `BIG-IP`_ device on a network to synchronize some or all of its configuration data among several BIG-IP devices; fail over to one of many available devices; and/or mirror connections to a peer device to prevent interruption in service during failover.

    device group
        A device group is a component of a device service cluster. It consists of a collection of `BIG-IP`_ devices that trust each other and can synchronize, and sometimes fail over, their configuration data.

    high availability
    highly available
    HA
        The ability of a `BIG-IP`_ device to process network traffic successfully. An HA device is generally part of a :term:`device cluster`.

    pair
        Two (2) `BIG-IP`_ devices configured to use the :term:`active-standby` :term:`HA` mode.

    scalen
        Two (2) or more `BIG-IP`_ devices configured as an active :term:`device cluster`.

    active-active
        Both `BIG-IP`_ devices in a :term:`pair` are in an active state, processing traffic for different virtual servers or SNATs. If one device :term:`fails over`, the remaining device processes traffic from the failed device in addition to its own traffic.

    active-standby
    active-standby pair
        Only one of the two `BIG-IP`_ devices is in an active state -- that is, processing traffic -- at any given time. If the active device :term:`fails over`, the second device enters active mode and processes traffic that was originally targeted for the primary device.

    failover
    fail over
    fails over
        Failover occurs when one device in an :term:`active-standby` pair becomes unavailable; the secondary device processes traffic that was originally targeted for the primary device.

    mirror
    mirroring
        A `BIG-IP`_ system redundancy feature that ensures connection and persistence information is shared to another device in a device service cluster; mirroring helps prevent service interruptions if/when :term:`failover` occurs.

    SSL offloading
        SSL offloading relieves a Web server of the processing burden of encrypting and/or decrypting traffic sent via SSL, the security protocol that is implemented in every Web browser. For more information, see the `F5 Glossary <https://f5.com/glossary/ssl-offloading>`_.

    one-arm
    one-arm mode
        One-arm mode is a network topology wherein servers/clients connect to the BIG-IP via a single interface; a single VLAN handles all traffic.

    multi-arm
    multiple-arm
    multi-arm mode
    multiple-arm mode
        Multi-arm mode is a network topology wherein servers/clients connect to the BIG-IP via different interfaces; two or more VLANs can be used to handle management and data traffic.
    vcmp
        Virtual Clustered Multiprocessing (vCMP) is a feature of the BIG-IP system that allows you to run multiple instances of the BIG-IP software on a single hardware platform.
    vCMP host
        The vCMP host is the system-wide hypervisor that makes it possible for you to create and view BIG-IP instances, or vCMP 'guests'.
    vCMP guest
        A vCMP guest is an instance of BIG-IP software created on the vCMP system for the purpose of provisioning one or more BIG-IP modules to process application traffic.



.. _BIG-IP: https://f5.com/products/big-ip
