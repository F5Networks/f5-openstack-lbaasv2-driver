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

.. important::

    The Neutron configurations required may differ depending on your OS. Please see our partners' documentation for more information.

    - `Hewlett Packard Enterprise <http://docs.hpcloud.com/#3.x/helion/networking/lbaas_admin.html>`_
    - `Mirantis <https://www.mirantis.com/partners/f5-networks/>`_
    - `RedHat <https://access.redhat.com/ecosystem/software/1446683>`_
    

.. include:: includes/topic_start-f5-agent.rst
    :start-line: 4

Next Steps
==========

- See the :ref:`Coding Example` for the commands to use to configure basic load balancing via the Neutron CLI.
- See :ref:`F5 LBaaSv2 to BIG-IP Configuration Mapping` to discover what the F5 agent configures on the BIG-IP.


.. _license: https://f5.com/products/how-to-buy/simplified-licensing
.. _OpenStack Networking Concepts: http://docs.openstack.org/newton/networking-guide/

