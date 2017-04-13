:orphan: true

.. _device-driver-settings:

Device Driver Settings / iControl Driver Settings
=================================================

Overview
--------

The Device Driver Settings in the :ref:`Agent Configuration File` provide the means of communication between the F5 agent and BIG-IP device(s). **Do not change this setting**.

The iControl Driver Settings identify the BIG-IP device(s) that you want the F5 agent to manage and record the login information the agent will use to communicate with the BIG-IP(s).

Use Case
--------

If you want to use the F5 agent to manage BIG-IP from within your OpenStack cloud, you **must** provide the correct information in this section of the agent config file. The F5 agent can manage a :term:`standalone` device or a :term:`device service cluster`.

.. seealso:: :ref:`Manage BIG-IP Clusters with F5 LBaaSv2`


Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.

- Operational OpenStack cloud (|openstack| release).

- Administrator access to both BIG-IP device(s) and OpenStack cloud.

- Basic understanding of `BIG-IP system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.

- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` installed on the Neutron controller and all other hosts for which you want to provision LBaaS services.


Caveats
-------

- vCMP is unsupported in this release (v |release|).
- Clustering is limited to two (2) BIG-IP devices in this release.


Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-block:: text

    $ sudo vi /etc/neutron/services/f5/f5-openstack-agent.ini

2. Enter the iControl endpoint(s), username, and password for your BIG-IP(s).

    * ``icontrol_hostname``: The IP address(es) of the BIG-IP(s) the agent will manage. If you're using multiple devices, provide a comma-separated list containing the management IP address of each device.
    * ``icontrol_vcmp_hostname``: *Unsupported in this release*.
    * ``icontrol_username``: The username of the adminstrative user; *must have access to all BIG-IP devices*.
    * ``icontrol_password``: The password of the adminstrative user; *must have access to all BIG-IP devices*.

.. topic:: Example

    .. code-block:: text
        :emphasize-lines: 17, 31, 36

        ###############################################################################
        #  Device Driver - iControl Driver Setting
        ###############################################################################
        #
        # This setting can be either a single IP address or a
        # comma separated list containing all devices in a device
        # service group.
        #
        # If a single IP address is used and the HA model
        # is not standalone, all devices in the sync failover
        # device group for the hostname specified must have
        # their management IP address reachable to the agent.
        # In order to access devices' iControl interfaces via
        # self IPs, you should specify them as a comma
        # separated list below.
        #
        icontrol_hostname = 10.190.7.232 \\ replace with the IP address(es) of your BIG-IP(s)
        #
        # If you are using vCMP with VLANs, you will need to configure
        # your vCMP host addresses, in addition to the guests addresses.
        # vCMP Host access is necessary for provisioning VLANs to a guest.
        # Use icontrol_hostname for vCMP guests and icontrol_vcmp_hostname
        # for vCMP hosts. The agent will automatically determine
        # which host corresponds to each guest.
        #
        # icontrol_vcmp_hostname = 192.168.1.245
        #
        # icontrol_username must be a valid Administrator username
        # on all devices in a device sync failover group.
        #
        icontrol_username = admin
        #
        # icontrol_password must be a valid Administrator password
        # on all devices in a device sync failover group.
        #
        icontrol_password = admin
        #


.. Further Reading
    ---------------





