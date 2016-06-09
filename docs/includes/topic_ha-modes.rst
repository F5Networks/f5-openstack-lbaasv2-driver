.. _ha-mode:

HA mode
```````

- ``f5_ha_type``: Defines the high availability (HA) mode used by the BIG-IP®.

    * ``standalone``: Single BIG-IP® device; no HA.
    * ``pair``: Active/standby two device HA.
    * ``scalen``: Active device cluster.

    .. code-block:: text

        # HA model
        #
        # ...
        #
        f5_ha_type = standalone \\ pair \\ scalen
        #
        #





