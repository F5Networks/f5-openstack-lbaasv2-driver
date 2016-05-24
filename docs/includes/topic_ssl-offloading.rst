.. _ssl-offloading:

SSL Offloading
--------------

Overview
````````

`SSL offloading <https://f5.com/glossary/ssl-offloading>`_ relieves a Web server of the processing burden of encrypting and/or decrypting traffic sent via SSL, the security protocol that is implemented in every Web browser. The processing is offloaded to a separate device designed specifically to perform `SSL acceleration <https://f5.com/glossary/ssl-acceleration/>`_ or `SSL termination <https://f5.com/glossary/ssl-termination/>`_.

In Neutron LBaaSv2, the F5® agent manages SSL offloading functionality on BIG-IP® via the LBaaSv2 TLS, or ``TERMINATED HTTPS``, feature.

Prerequisites
`````````````

The following prerequisites must be met before you can set up the the F5® LBaaSv2 plugin to use SSL termination. These are in addition to the basic prerequisites described in :ref:`Before You Begin <before-you-begin>`.

* `OpenStack Barbican Key Manager <https://wiki.openstack.org/wiki/Barbican>`_ must be installed and configured to work with the `OpenStack Keystone identity service <http://docs.openstack.org/developer/keystone/index.html>`_.
* At least one Barbican container exists, with at least one certificate chain and key.
* Familiarity with the `barbican api commands <http://docs.openstack.org/developer/barbican/api/>`_ (show examples)

.. seealso::

    * `OpenStack Security Guide <http://docs.openstack.org/security-guide/secure-communication.html>`_: Describes the rationales for using SSL/TLS in greater depth and provides example reference architectures and use cases.

    * `OpenStack Barbican User API Guide <http://developer.openstack.org/api-guide/key-manager/>`_

    * `OpenStack Wiki: How to create a tls-enabled load balancer <https://wiki.openstack.org/wiki/Network/LBaaS/docs/how-to-create-tls-loadbalancer>`_


Configure Neutron to use Key Manager
````````````````````````````````````

Update Neutron config file
~~~~~~~~~~~~~~~~~~~~~~~~~~

Add or update the 'service_auth' group in :file:`/etc/neutron/neutron_lbaas.conf`. This section is commented out (preceded by ``#``) by default.

.. topic:: Example:

    .. code-block:: text

        $ vi /etc/neutron/neutron_lbaas.conf

        [service_auth]
        auth_url = http://10.190.4.122:5000/v3
        admin_tenant_name = admin
        admin_user = admin
        admin_password = changeme
        admin_user_domain = default
        admin_project_domain = default
        region = RegionOne
        service_name = lbaas
        auth_version = 3


    .. important::

        * Be sure to use the correct values for your particular environment.


Configure the F5® Agent
````````````````````````

Edit :file:`/etc/neutron/services/f5/f5-openstack-agent.ini` to configure certificate manager authentication.

.. topic:: Example:

    .. code-block::

        ###############################################################################
        # Certificate Manager
        ###############################################################################
        cert_manager = f5_openstack_agent.lbaasv2.drivers.bigip.barbican_cert.BarbicanCertManager
        #
        # Two authentication modes are supported for BarbicanCertManager:
        #   keystone v2 and keystone v3
        #
        #
        # Keystone v2 authentication:
        #
        # auth_version = v2
        # os_auth_url = http://localhost:5000/v2.0
        # os_username = admin
        # os_password = changeme
        # os_tenant_name = admin
        #
        #
        # Keystone v3 authentication:
        #
        auth_version = v3
        os_auth_url = http://localhost:5000/v3
        os_username = admin
        os_password = changeme
        os_user_domain_name = default
        os_project_name = admin
        os_project_domain_name = default


.. important::

    * Be sure to use the correct values (username, password, etc.) for your particular environment.

    * Be sure you have ``auth_version`` set to use the version of Keystone that you're using (v2 or v3). The example shows a configuration for Keystone v3. To use v2, change ``auth_version`` to v2; comment out (``#``) the v3 items; and uncomment the v2 items.


Restart the Neutron server and F5® agent
````````````````````````````````````````

Restart the Neutron server and F5® agent to make the changes take effect.

.. code-block:: shell

    $ sudo service neutron-server restart                 \\ Debian/Ubuntu
    $ sudo service f5-oslbaasv2-agent restart

    $ sudo systemctl restart neutron-server                \\ RedHat/CentOS
    $ sudo systemctl restart f5-openstack-agent







