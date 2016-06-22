:orphan: true

.. _global-routed-mode:

Global Routed Mode
==================

Overview
--------


Use Case
--------



Prerequisites
-------------

-
-
-


Caveats
-------

-
-
-


Configuration
-------------


Further Reading
---------------

.. seealso::

    * x
    * y
    * z




Setting ``f5_global_routed_mode`` to ``true`` causes the agent to assume that all VIPs and pool members will be reachable via global device L3 routes, which must be already provisioned on the BIG-IP®s. Set this option to ``false`` if you wish to use L2/L3 segmentation.

    .. code-block:: text

        # Global Routing Mode - No L2 or L3 Segmentation on BIG-IP®
        #
        # This setting will cause the agent to assume that all VIPs
        # and pool members will be reachable via global device
        # L3 routes, which must be already provisioned on the BIG-IP®s.
        #
        # ...
        #
        f5_global_routed_mode = True
        #
