.. _install-f5-lbaasv2-driver:

Install the F5® LBaaSv2 Driver
------------------------------

.. include:: topic_tip-sudo-pip-git.rst

.. topic:: To install the ``f5-openstack-lbaasv2-driver`` package:

    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver


.. important::

    The command above will install the package from the default branch (liberty). You can install specific releases by adding ``@<release_tag>`` to the end of the install command.

    For example:

    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@v8.0.3

