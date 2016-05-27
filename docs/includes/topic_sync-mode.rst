.. _sync-mode:

Sync mode
`````````

* ``f5_sync_mode``: Defines the model by which policies configured on one BIG-IP® are shared with other BIG-IP®s.

   * ``autosync``: configurations are synced automatically across all BIG-IP®s in a device cluster. [#fn1]_
   * ``replication``: each device is configured separately.

    .. code-block:: text

        # Sync mode
        #
        # ...
        #
        f5_sync_mode = replication
        #


