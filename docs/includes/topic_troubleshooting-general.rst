Troubleshooting
---------------

To troubleshoot general problems, set the Neutron and the F5® agent ``debug`` setting to ``True``.

Extensive logging will then appear in the ``neutron-server`` and ``f5-oslbaasv1-agent`` log files on their respective hosts.

.. topic:: Set the DEBUG log level output for the f5-openstack-agent:

    .. code-block:: text

        $ vi /etc/neutron/services/f5/f5-openstack-agent.ini

        #
        [DEFAULT]
        # Show debugging output in log (sets DEBUG log level output).
        debug = True
        ...


.. topic:: Set the DEBUG log level output for Neutron:

    .. code-block:: text

        $ vi /etc/neutron/neutron.conf
        DEBUG = T

