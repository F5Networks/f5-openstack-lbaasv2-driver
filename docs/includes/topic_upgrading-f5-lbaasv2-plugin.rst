:orphan: true

Upgrading the F5 LBaaSv2 Components
===================================

If you are upgrading from an earlier version, F5® recommends that you uninstall the current version, then install the new version.

.. warning::

    Using ``pip install --upgrade`` to upgrade the F5 LBaaSv2 agent can impact packages that are used by other OpenStack components. We strongly urge all users to follow these instructions instead.


To upgrade, perform the following steps on every server on which the F5 agent is running.


Make a copy of the F5 agent configuration file
----------------------------------------------

The existing configuration file in */etc/neutron/services/f5/* will be overwritten when you install the new package.

    .. code-block:: text

        $ cp /etc/neutron/services/f5/f5-openstack-agent.ini ~/

Stop and remove the current version of the F5 agent
---------------------------------------------------

Debian/Ubuntu
`````````````

.. code-block:: text

    $ sudo service f5-oslbaasv2-agent stop
    $ pip uninstall f5-openstack-agent


Red Hat/CentOS
``````````````

.. code-block:: text

    $ sudo systemctl stop f5-openstack-agent
    $ sudo systemctl disable f5-openstack-agent
    $ sudo pip uninstall f5-openstack-agent


Install the new version of the F5 agent
---------------------------------------

Follow the :ref:`agent <agent:home>` and installation instructions to install the version to which you'd like to upgrade.

Restore the F5 agent configuration file
---------------------------------------

Compare the backup file with the new one created during installation to make sure only the necessary settings for your deployment are modified. Then, copy your configuration file back into */etc/neutron/services/f5*.

.. code-block:: text

    $ cp ~/f5-openstack-agent.ini /etc/neutron/services/f5/f5-openstack-agent.ini

