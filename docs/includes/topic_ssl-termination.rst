.. _topic_ssl-termination:

SSL Termination
---------------

Overview
````````

'SSL termination' refers to the process that occurs at the server end of an SSL connection, where the traffic transitions between encrypted and unencrypted forms. In Neutron LBaaSv2, the SSL/TLS feature provides a means of securing communication over OpenStack-managed networks.

Prerequisites
`````````````

The following prerequisites must be met before you can set up the the F5® LBaaSv2 plugin to use SSL termination. These are in addition to the basic requirements described in :ref:`Before You Begin <lbaasv2-deployment-before-you-begin>`.

* `OpenStack Barbican Key Manager <https://wiki.openstack.org/wiki/Barbican>`_ must be installed and configured to work with the `OpenStack Keystone identity service <http://docs.openstack.org/developer/keystone/index.html>`_.
* Create at least one Barbican container with at least one certificate chain and key; note the URL for the container, as it will be needed to create the ssl-enabled load balancer.
* Familiarity with the `barbican api commands <http://docs.openstack.org/developer/barbican/api/>`_ (show examples)


Configure Neutron to use Key Manager
````````````````````````````````````

Update Neutron config file
~~~~~~~~~~~~~~~~~~~~~~~~~~

Add or update the 'service_auth' group in :file:`/etc/neutron/neutron_lbaas.conf`. This section is commented out (preceded by ``#``) by default.

.. code-block:: text

    $ vi /etc/neutron/neutron_lbaas.conf

    service_auth
    auth_uri = http://localhost:35357/v2.0
    admin_tenant_name = admin
    admin_user = admin
    admin_password = password
    auth_version = 2


.. note::

    * Be sure to use the correct values for your particular environment.


Restart Neutron server and F5® agent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    $ sudo service neutron-server restart                 \\ Debian/Ubuntu
    $ sudo service f5-oslbaasv2-agent restart

    $ sudo systemctl restart neutron-server                \\ RedHat/CentOS
    $ sudo systemctl restart f5-openstack-agent


Using SSL Termination with the F5® LBaaSv2 Plugin
`````````````````````````````````````````````````

For high availability or load balanced deployments, the F5® agent extracts the cert and key from the Barbican container, then uses it to create an SSL profile for the virtual server on the BIG-IP®. This is done via the ``neutron lbaas-listener-create`` CLI command, as shown in the example below.

.. note::

    You need to source a :file:`keystonerc` file with admin credentials to use the ``neutron`` command set.


.. topic:: Example

    $ neutron lbaas-listener-create --loadbalancer lb1 --protocol-port 443 --protocol TERMINATED_HTTPS --name listener1 --default-tls-container=<container_URL>




.. seealso::

    * `OpenStack Security Guide <http://docs.openstack.org/security-guide/secure-communication.html>`_: Describes the rationales for using SSL/TLS in greater depth and provides example reference architectures and use cases.

    * `OpenStack Barbican User Guide <http://developer.openstack.org/api-guide/key-manager/>`_

    * `OpenStack Wiki: How to create a tls-enabled load balancer <https://wiki.openstack.org/wiki/Network/LBaaS/docs/how-to-create-tls-loadbalancer>`_

