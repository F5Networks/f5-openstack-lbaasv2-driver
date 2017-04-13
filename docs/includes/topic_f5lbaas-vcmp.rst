F5 LBaaSv2 and vCMP
===================

Overview
--------

Virtual Clustered Multiprocessing™ (vCMP) is a feature of the BIG-IP system that allows you to run multiple instances of BIG-IP software on a single hardware platform. vCMP allocates a specific share of the hardware resources to each BIG-IP instance, or :term:`vCMP guest`.

A vCMP guest consists of a TMOS instance and one or more BIG-IP modules. The :term:`vCMP host` allocates a share of the hardware resources to each guest; each guest also has its own management IP address, self IP addresses, virtual servers, and so on. In this way, each guest can effectively receive and process application traffic with no knowledge of other guests on the system.

F5 LBaaSv2 allows you to manage vCMP guests in the same way that you would a physical BIG-IP device or BIG-IP Virtual Edition. See the :ref:`Configuration` section for details.


Use Case
--------

When used with vCMP in a flat network or VLAN, the F5 agent can manage one or more vCMP hosts, each of which can have one or more guests. Guests on the same, or different, vCMP hosts can be configured to operate as a :term:`device service cluster`. If a vCMP host fails (taking its guests with it), another vCMP host with guests configured as part of the cluster can take over managing its traffic. This provides a high degree of redundancy, while requiring fewer physical resources. vCMP also allows you to delegate management of the BIG-IP software in each instance to individual administrators. This means users who need to manage LBaaS objects don't need to be given full administrative access to the BIG-IP, only to the host & guests allotted for their project(s).

Prerequisites
-------------

- Licensed, operational BIG-IP chassis with support for vCMP.
- Licensed, operational BIG-IP vCMP guest running on a vCMP host.
- Operational OpenStack cloud (|openstack| release).
- Administrative access to the vCMP host(s) and guest(s) you will manage with F5 LBaaSv2.
- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` installed on the Neutron controller.
- Knowledge of `BIG-IP vCMP <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/vcmp-administration-appliances-12-1-1/1.html>`_ configuration and administration.

Caveats
-------

- In release v |release| of the F5 LBaaSv2 driver and agent, ``VLAN`` and ``FLAT`` are the only ML2 network types supported for use with vCMP.


Configuration
-------------

#. Edit the :ref:`Agent Configuration File`.

#. Add the ``icontrol_vcmp_hostname``. Multiple values can be comma-separated.

    .. code-block:: text
        :emphasize-lines: 8

        # If you are using vCMP with VLANs, you will need to configure
        # your vCMP host addresses, in addition to the guests addresses.
        # vCMP Host access is necessary for provisioning VLANs to a guest.
        # Use icontrol_hostname for vCMP guests and icontrol_vcmp_hostname
        # for vCMP hosts. The plug-in will automatically determine
        # which host corresponds to each guest.
        #
        icontrol_vcmp_hostname = 192.168.1.245
        #

#. Configure the ``icontrol_hostname`` parameter with the IP address(es) of the vCMP guest(s):

    .. code-block:: text
        :emphasize-lines: 19

        ###############################################################################
        #  Device Driver - iControl Driver Setting
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
        # If order to access devices' iControl interfaces via
        # self IPs, you should specify them as a comma
        # separated list below. 
        #
        icontrol_hostname = 10.190.7.232, 10.190.4.51
        #

#. Set the ``advertised_tunnel_types`` parameter to ``vlan`` or ``flat``, as appropriate for your environment.

    .. important::

        If the ``advertised_tunnel_types`` setting in the Agent Configuration File is left empty, as in the example below, the ``provider:network_type`` in the ML2 plugin should be set to FLAT or VLAN.


    **Example:**

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
         #


Further Reading
---------------

.. seealso::

    * See the `BIG-IP vCMP documentation`_ for more information about vCMP.

.. _BIG-IP vCMP documentation: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/vcmp-administration-appliances-12-1-1/1.html?sr=57167911



