vCMP
=====

Overview
--------

Virtual Clustered Multiprocessing™ (vCMP®) is a feature of the BIG-IP® system that allows you to run multiple instances of the BIG-IP® software on a single hardware platform. vCMP allocates a specific share of the hardware resources to each BIG-IP® instance, or vCMP guest. Each guest that you create behaves as a separate BIG-IP® device, having its own CPU, memory, and disk space. Each guest also has its own configuration file, log files, and kernel instance.

vCMP is built on F5 Networks' CMP technology. CMP works with cluster members. Cluster members can be slots within a chassis or instances of the Traffic Management Microkernel (TMM) on an appliance. CMP allows cluster members to work together to form a coherent, distributed traffic-processing system to share traffic load. vCMP takes this one step further by allowing you to create and run virtualized BIG-IP® modules, using a standards-based, purpose-built hypervisor.

The f5-openstack-agent supports device configuration of vCMP guests which are hosted on a vCMP host, as defined above. The Guest is essentially a BIG-IP® virtual machine guest.

Use Case
--------

vCMP is important for VLAN and flat network configurations. When using vCMP in either of these network deployments, the operation of the agent is the same, a VLAN is created on the vCMP host and associated with the Guest (provided by the ``icontrol_hostname`` setting in the Agent Configuration File). vCMP guests can also be a part of a :term:`device service cluster` across term:`vCMP hosts`. This can be useful for maximum redundancy in case a :term:`vCMP host` were to fail (and the guests along with it), the other :term:`vCMP host`, which has guest(s) that are part of the :term:`device service cluster` can takeover managing the traffic for the failed guests.

Prerequisites
-------------

- Licensed, operational BIG-IP chassis with support for vCMP :term:`vCMP host`
- Licensed, operational BIG-IP vCMP guest running on a vCMP host :term:`vCMP guest`
- Operational OpenStack cloud (|openstack| release).
- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <install-f5-lbaasv2-driver>` installed on the Neutron controller and all other hosts for which you want to provision LBaaS services.

Caveats
-------

- In release v |release| of the F5 LBaaSv2 driver and agent, ``VLAN`` and ``FLAT`` are the only supported ML2 network types when using vCMP.


Configuration
-------------

1. Edit the :ref:`Agent Configuration File`:

.. code-blocks:: text

    $ sudo emacs /etc/neutron/services/f5/f5-openstack-agent.ini

2. Configure the icontrol_vcmp_hostname setting to identify the vCMP host(s):

.. topic:: Example

    .. code-block:: text
        :emphasize-lines 8

        # If you are using vCMP® with VLANs, you will need to configure
        # your vCMP® host addresses, in addition to the guests addresses.
        # vCMP® Host access is necessary for provisioning VLANs to a guest.
        # Use icontrol_hostname for vCMP® guests and icontrol_vcmp_hostname
        # for vCMP® hosts. The plug-in will automatically determine
        # which host corresponds to each guest.
        #
        icontrol_vcmp_hostname = 192.168.1.245

3. Configure the icontrol_hostname setting to identify the vCMP guest(s):

.. topic:: Example

    .. code-block:: text
        :emphasize-lines 19

        ###############################################################################
        #  Device Driver - iControl® Driver Setting
        ###############################################################################
        #
        # icontrol_hostname is valid for external device type only.
        # this setting can be either a single IP address or a 
        # comma separated list contain all devices in a device 
        # service group.  For guest devices, the first fixed_address
        # on the first device interfaces will be used.
        #
        # If a single IP address is used and the HA model 
        # is not standalone, all devices in the sync failover
        # device group for the hostname specified must have 
        # their management IP address reachable to the agent.
        # If order to access devices' iControl® interfaces via
        # self IPs, you should specify them as a comma
        # separated list below. 
        #
        icontrol_hostname = 10.190.7.232

4. Set the advertised_tunnel_types setting to identify use of vlan:

.. topic:: Example

    .. code-block:: text
        :emphasize-lines: 10

     # Tunnel types
     #
     # This is a comma separated list of tunnel types to report
     # as available from this agent as well as to send via tunnel_sync
     # rpc messages to compute nodes. This should match your ml2
     # network types on your compute nodes.
     #
     # If you are using only vlans only it should be:
     #
     advertised_tunnel_types =

Further Reading
---------------

.. seealso::

    * See :ref:`vCMP`
    * See :ref:`vCMP host`
    * See :ref:`vCMP guest`

.. _vCMP: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/vcmp-viprion-configuration-11-2-0/2.html



