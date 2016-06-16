:orphan: true

.. _sync-mode:

Sync mode
=========

* ``f5_sync_mode``: Defines the model by which policies configured on one BIG-IP® are shared with other BIG-IP®s.

   * ``replication``: the agent configures each device in a cluster directly, in real time.

    .. code-block:: text

        # Sync mode
        #
        # ...
        #
        f5_sync_mode = replication
        #


