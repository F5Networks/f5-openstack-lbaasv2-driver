.. _lbaasv2-deploy-before-you-begin:

Before You Begin
----------------

Prerequisites
`````````````

In order to follow this guide, you will need the following:

* A functional OpenStack |openstack| environment with at least one controller node, one compute node, and one network node.
* An undercloud [#f1]_ or overcloud [#f2]_ BIG-IP® deployment.
* Basic understanding of OpenStack networking concepts. See the `OpenStack docs <http://docs.openstack.org/liberty/>`_ for more information.
* F5® service provider package installed on Neutron controller (see below).


.. [#f1] BIG-IP® VE deployed as an OpenStack instance
.. [#f2] BIG-IP® VE or hardware deployed outside of OpenStack


Install the F5® Service Provider Package
````````````````````````````````````````

Install the F5® LBaaSv2 service provider package *before* you :ref:`install the F5® LBaaSv2 plugin packages <install-f5-agent-driver>`. If the F5® service provider package isn't present on your Neutron controller,  the F5® agent and LBaaSv2 driver will not work.

.. topic:: Download the F5® LBaaSv2 service provider package and add it to the python path for ``neutron_lbaas``.

    1. Download from GitHub

    .. code-block:: shell

        $ curl -O -L https://github.com/F5Networks/neutron-lbaas/releases/download/v8.0.1/f5.tgz


    2. Install the service provider package.

    a. CentOS:

    .. code-block:: text

        $ sudo tar xvf f5.tgz -C /usr/lib/python2.7/site-packages/neutron_lbaas/drivers/

    b. Ubuntu:

    .. code-block:: text

        $ sudo tar xvf f5.tgz –C /usr/lib/python2.7/dist-packages/neutron_lbaas/drivers/
