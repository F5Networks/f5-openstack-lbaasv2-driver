:orphan: true

Before You Begin
================

In order to use this guide, you will need the following:

- Operational OpenStack cloud (|openstack| release).

- Licensed, operational BIG-IP® :term:`device` or :term:`device cluster`; can be deployed either :term:`overcloud` or :term:`undercloud`.

- Basic understanding of OpenStack networking concepts. See the `OpenStack docs <http://docs.openstack.org/liberty/>`_ for more information.

- Basic understanding of `BIG-IP® Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

- F5® :ref:`service provider package <Install the F5 Service Provider Package>` installed on Neutron controller.


Install the F5 Service Provider Package
---------------------------------------

Install the F5 LBaaSv2 service provider package *before* you install the F5 LBaaSv2 driver. If the F5 service provider package isn't present on your Neutron controller, the F5 LBaaSv2 driver will not work.

.. topic:: Download the F5 LBaaSv2 service provider package and add it to the python path for ``neutron_lbaas``.

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


Install the F5 Agent
--------------------

See the :ref:`F5 Agent documentation <agent:home>` for installation instructions.

The F5 agent should, at minimum, be installed on your Neutron controller. You can also install it on any host for which you'd like to provision BIG-IP services.


..  todo: add footnote: See :ref:`Environment Recommendations`
