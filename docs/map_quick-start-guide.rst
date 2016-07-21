F5 LBaaSv2 Quick Start Guide
############################

.. include:: map_before-you-begin.rst


Configure F5 LBaaSv2
====================

.. include:: includes/topic_config-agent-overview.rst
    :start-line: 4

The table below contains a summary of the recommended F5 LBaaSv2 :ref:`configuration settings <Configure the F5 OpenStack Agent>`.

.. note:: This table is not a comprehensive list of all available options. For additional information, and to view all available configuration options, please see :ref:`Supported Features`.

.. include:: includes/ref_agent-config-settings-table.rst
    :start-line: 5

.. include:: includes/ref_agent-config-file.rst
    :start-after: each available configuration option.
    :end-before: :ref:`Global Routed Mode

* :ref:`Global Routed Mode` :download:`f5-openstack-agent.grm.ini <_static/f5-openstack-agent.grm.ini>`

* GRE tunnels :download:`f5-openstack-agent.gre.ini <_static/f5-openstack-agent.gre.ini>`

* VxLAN tunnels :download:`f5-openstack-agent.vxlan.ini <_static/f5-openstack-agent.vxlan.ini>`

* Tagged VLANs (without tunnels) :download:`f5-openstack-agent.vlan.ini <_static/f5-openstack-agent.vlan.ini>`



.. include:: includes/topic_configure-neutron-lbaasv2.rst
    :start-line: 4


.. _license: https://f5.com/products/how-to-buy/simplified-licensing
.. _OpenStack Networking Concepts: http://docs.openstack.org/liberty/networking-guide/

