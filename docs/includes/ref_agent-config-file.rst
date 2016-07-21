:orphan: true

Agent Configuration File
========================

The agent configuration file -- :file:`/etc/neutron/services/f5/f5-openstack-agent.ini` -- controls how the agent interacts with your BIG-IP®(s). The file contains detailed descriptions of each available configuration option.

For reference, we've provided here a set of 'pre-configured' agent config files. These examples can help guide you in setting up the F5 agent to work with your specific environment.

:ref:`Global Routed Mode`
-------------------------

Can be used for :term:`standalone`, :term:`overcloud` BIG-IP® VE deployments.

* :download:`f5-openstack-agent.grm.ini <../_static/f5-openstack-agent.grm.ini>`


:ref:`L2 Adjacent Mode`
-------------------------------

Can be used for :term:`standalone` or :term:`clustered` :term:`undercloud` BIG-IP® hardware or VE deployments.

* :download:`f5-openstack-agent.gre.ini <../_static/f5-openstack-agent.gre.ini>`

* :download:`f5-openstack-agent.vlan.ini <../_static/f5-openstack-agent.vlan.ini>`

* :download:`f5-openstack-agent.vxlan.ini <../_static/f5-openstack-agent.vxlan.ini>`


