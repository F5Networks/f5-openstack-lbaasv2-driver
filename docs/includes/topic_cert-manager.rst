Certificate Manager
===================

Overview
--------

OpenStack's 'Barbican' certificate manager provides a secure location where users can store sensitive information, such as SSH keys, private keys, certificates, and user passwords (referred to as "`secrets`_ " in OpenStack lingo).

The F5® agent allows users to use their Barbican certificates in conjunction with :term:`SSL offloading`, shifting client authentication and encryption/decryption tasks from the target server. It also allows users to designate an existing BIG-IP® SSL profile as the parent from which all client profiles created in OpenStack inherit settings.

Use Case
--------

In general, SSL offloading increases server and application capacity by moving authentication processing from the target server to a designated authentication server. When you configure  certificate manager in your OpenStack cloud, you can create LBaaS listeners that use the ``TERMINATED_HTTPS`` protocol for TLS/SSL termination. If you have already defined SSL profiles on your BIG-IP, you can designate one as the parent profile from which all of the client SSL profile settings will be inherited.


Prerequisites
-------------

- `OpenStack Barbican`_ certificate manager is configured and operational.
-
-


Caveats
-------

-
-
-


Configuration
-------------


Further Reading
---------------

.. seealso::

    * `BIG-IP SSL Administration Guide`_
    * y
    * z


.. _OpenStack Barbican:
.. _secrets: http://developer.openstack.org/api-guide/key-manager/secrets.html
.. _BIG-IP SSL Administration Guide: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-ssl-administration-12-0-0.html?sr=54998771



```````````````````




- ``cert_manager``: The certificate manager that manages access to certificates and keys for user authentication. Must be set to ``f5_openstack_agent.lbaasv2.drivers.bigip.barbican_cert.BarbicanCertManager``.

- Keystone v2/v3 authentication

    - ``auth_version``: Keystone version (``v2`` or ``v3``)
    - ``os_auth_url``: Keystone authentication URL
    - ``os_username``: OpenStack username
    - ``os_password``: OpenStack password
    - ``os_tenant_name``: OpenStack tenant name (v2 only)
    - ``os_user_domain_name``: OpenStack domain in which the user account resides (v3 only)
    - ``os_project_name``: OpenStack project name (v3 only; refers to the same data as ``os_tenant_name`` in v2)
    - ``os_project_domain_name``: OpenStack domain in which the project resides
    - ``f5_parent_ssl_profile``: The parent SSL profile on the BIG-IP® from which the agent SSL profile should inherit settings

    .. code-block:: text

        #
        cert_manager = f5_openstack_agent.lbaasv2.drivers.bigip.barbican_cert.BarbicanCertManager \\ DO NOT CHANGE
        #
        # Two authentication modes are supported for BarbicanCertManager:
        #   keystone_v2, and keystone_v3
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
        #
        # Parent SSL profile name
        #
        # A client SSL profile is created for LBaaS listeners that use TERMINATED_HTTPS
        # protocol. You can define the parent profile for this profile by setting
        # f5_parent_ssl_profile. The profile created to support TERMINATTED_HTTPS will
        # inherit settings from the parent you define. This must be an existing profile,
        # and if it does not exist on your BIG-IP® system the agent will use the default
        # profile, clientssl.
        #f5_parent_ssl_profile = clientssl
        #

