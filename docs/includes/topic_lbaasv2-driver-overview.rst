Overview
--------

The F5® OpenStack LBaaSv2 service provider driver (also called the 'F5® LBaaSv2 driver') makes it possible to provision F5® BIG-IP® local traffic management (LTM®) services in an OpenStack cloud.

.. important::

    The F5® LBaaSv2 driver is not a standalone Neutron LBaaS plugin. Rather, it passes Neutron ``lbaas`` API calls to the :ref:`F5® agent <agent:home>`, which translates the calls into BIG-IP® REST API calls.

    **You must install and configure the F5® OpenStack agent and the F5® LBaaSv2 driver** in order to provision BIG-IP® services in your OpenStack cloud.


.. seealso::

    * :ref:`agent:install-the-f5-openstack-agent`
    * :ref:`agent:configure-the-f5-openstack-agent`

