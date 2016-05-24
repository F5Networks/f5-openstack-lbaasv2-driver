.. _install-f5-agent-driver:

Install the F5® Agent and Driver Packages
-----------------------------------------

.. note::

    - You must have both ``pip`` and ``git`` installed on your machine in order to use these commands.
    - It may be necessary to use ``sudo``, depending on your environment.

.. topic:: To install the ``f5-openstack-lbaasv2-driver`` and ``f5-openstack-agent`` packages:

    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver
        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-agent

.. important::

    The command above will install the package from the default branch (liberty). You can install specific releases by adding ``@<release_tag>`` to the end of the install command.

    For example:

    .. code-block:: text

        $ sudo pip install git+https://github.com/F5Networks/f5-openstack-lbaasv2-driver@v8.0.1

