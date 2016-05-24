.. _deployment-guide:

F5® OpenStack LBaaSv2 Plugin Deployment Guide
=============================================

.. toctree::
    :hidden:


Release
-------

.. include:: ../README.rst
    :start-line: 42
    :end-line: 44

Compatibility
-------------

.. include:: ../README.rst
    :start-line: 63
    :end-line: 65

.. _lbaasv2-deployment-before-you-begin:

Before You Begin
----------------

.. include:: includes/topic_before-you-begin.rst
    :start-line: 5

Installation
------------

.. include:: includes/topic_install-f5-lbaasv2-packages.rst
    :start-line: 5

Configuration
-------------

Neutron
```````

.. include:: includes/topic_configure-neutron-lbaasv2.rst
    :start-line: 3


F5® Agent
`````````

.. include:: includes/topic_configure-the-agent.rst
    :start-line: 3

.. include:: includes/topic_tip-stop-agent.rst
    :start-line: 3

Usage
-----

.. note::

    The OpenStack LBaaSv2 CLI commands begin with ``lbaas``. See the `OpenStack CLI documentation <http://docs.openstack.org/cli-reference/neutron.html>`_ for more information.

* :ref:`SSL Termination <topic_ssl-termination>`

* :ref:`Coding Example <coding-example-lbaasv2>`

* :ref:`Troubleshooting <troubleshooting>`

Restrictions
````````````

.. include:: includes/topic_restrictions.rst
    :start-line: 3



