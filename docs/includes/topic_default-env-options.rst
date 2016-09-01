Default Environment
```````````````````

The F5® OpenStack LBaaSv2 plugin provides one default environment name, Project, as defined in the excerpt from :file:`/etc/neutron/services/f5/f5-openstack-agent.ini` below, the
agent's unique ``environment_prefix`` defines the environment to which it belongs.  Additionally, an environment can be serviced by mulitple device service groups by assigning a
``environment_group_number`` to each.  Each agent associated with a specific device service group should have the same ``environment_group_number``.  See capacity based scale out.


.. code-block:: shell

    ###############################################################################
    #  Environment Settings
    ###############################################################################
    #
    # Since many TMOS® object names must start with an alpha character
    # the environment_prefix is used to prefix all service objects.
    #
    # environment_prefix = 'Project'
    #
	# environment_group_number = 1
	#

After making changes to  :file:`/etc/neutron/service/f5f5-openstack-agent.ini` and :file:`/etc/neutron/neutron_lbaas.conf`, restart the ``neutron-server`` process.

