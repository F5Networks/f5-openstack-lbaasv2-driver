:orphan: true

F5 LBaaSv2 Quick Start Guide
============================

.. include:: topic_before-you-begin.rst
    :start-line: 5
    :end-before: Install the F5 Agent

Install the F5 Agent
--------------------

.. topic:: To install the ``f5-openstack-agent`` package for v |release|:

    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@<release_tag>



Install the F5 LBaaSv2 Driver
-----------------------------

.. include:: topic_install-f5-lbaasv2-driver.rst
    :start-line: 5


Configuration
=============

The table below contains a summary of the recommended F5 LBaaSv2 :ref:`configuration settings <Agent Configuration File>`.

.. note:: This table is not a comprehensive list of all available options. For additional information, and to view all available configuration options, please see :ref:`Supported Features`.

.. include:: ref_agent-config-settings-table.rst
    :start-line: 5




.. _license: https://f5.com/products/how-to-buy/simplified-licensing
.. _OpenStack Networking Concepts: http://docs.openstack.org/liberty/networking-guide/

