.. _device-driver-settings:

Device Driver / iControl® Driver Settings
`````````````````````````````````````````

* The device driver setting defines the driver that's used to communicate with BIG-IP®. **Do not** change this entry.

* The iControl® Driver settings identify the BIG-IP®(s) that the agent is expected to manage.

 .. important::

    You must provide the correct information -- including the a valid management IP address and credentials for a user with admin permissions on the BIG-IP® -- in this section or the F5® agent will not start.


    .. code-block:: text

        f5_bigip_lbaas_device_driver = f5_openstack_agent.lbaasv2.drivers.bigip.icontrol_driver.iControlDriver \\ DO NOT CHANGE
        #
        ...
        #
        icontrol_hostname = 10.190.7.232 \\ replace with the IP address of your BIG-IP®
        #
        #
        icontrol_username = admin
        #
        #
        icontrol_password = admin

