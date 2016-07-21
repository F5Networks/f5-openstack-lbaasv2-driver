:orphan: true

.. _topic-start-the-agent:

Start the F5® OpenStack Agent
=============================

Once you have configured the F5® agent as appropriate for your environment, use the command(s) appropriate for your OS to start the agent.

Debian/Ubuntu
-------------

.. code-block:: text

    $ sudo service f5-oslbaasv2-agent start


RedHat/CentOS
-------------

.. code-block:: text

    $ sudo systemctl enable f5-openstack-agent
    $ sudo systemctl start f5-openstack-agent


