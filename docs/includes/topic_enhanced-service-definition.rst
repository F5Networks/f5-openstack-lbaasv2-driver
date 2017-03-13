.. _esd:

Enhance L7 Policy Capabilites with Enhanced Service Definitions
===============================================================

.. versionadded:: 9.3.0

Overview
--------

BIG-IP has many load balancing configurations that don't have direct implementation in the OpenStack LBaaSv2 specification. While it's easy to customize BIG-IP local traffic management settings using `profiles`_, `policies`_, and `iRules`_, LBaaSv2 doesn't provide a way to apply these to BIG-IP virtual servers. Enhanced Service Definitions (ESDs) allow you to apply BIG-IP LTM `profiles`_, `policies`_, and `iRules`_ to OpenStack load balancers.

.. sidebar:: Helpful Hints

    1. Use a JSON lint application to validate your ESD files.
    2. Restart the F5 LBaaSv2 agent (f5-openstack-agent) every time you add or modify ESD files.
    3. Use a unique name for each ESD you define. ESD names are case-sensitive.
    4. Configure all `profiles`_, `policies`_, and/or `iRules`_ in the ``/Common`` partition on your BIG-IP **before** deploying your ESD.
    5. Remember that **ESDs overwrite existing settings**.
    6. When using `iRules`_ and `policies`_, remember that any iRule priority must be defined in the iRule itself.
    7. If you have DEBUG logging enabled, :ref:`check the agent log <set-log-level-debug>` for statements reporting on tag validity.

How ESDs Work
`````````````

An ESD is a set of tags and values that define custom settings for BIG-IP objects. Typically, an ESD applies one or more profiles, policies, or iRules to a BIG-IP virtual server. The F5 agent reads all ESD JSON files located in :file:`/etc/neutron/services/f5/esd/` on startup.

The F5 agent applies ESDs to BIG-IP virtual servers using LBaaSv2 `L7 policy`_ operations. When you create an LBaaSv2 L7 policy object (``neutron lbaas-l7policy-create``), the agent checks the policy name against the names of all available ESDs. If it finds a match, the agent applies the ESD to the BIG-IP virtual server associated with the policy. If the agent doesn't find a matching ESD, it creates a standard L7 policy. Essentially, the F5 agent supersedes the standard LBaaSv2 behavior, translating ``neutron lbaas-l7policy-create mypolicy`` into “apply the mypolicy ESD to the BIG-IP”.

You can define multiple ESDs, each of contains a set of predefined tags and values, in a single JSON file. The agent validates each tag and discards any that are invalid. ESDs remain fixed in agent memory until an agent is restarted.
When you apply multiple L7 policies, each subsequent ESD overwrites the virtual server settings defined by previous ESDs. For this reason, we recommend that you define all settings you want to apply for a specific application in a single ESD. If you define multiple ESDs, each should apply to one (1) specific application.

:ref:`Deleting an L7 policy that matches an ESD <esd-delete>` removes all ESD settings from the virtual server, returning the virtual server to its original state.

.. caution::

    The F5 agent ignores all ESD files that aren't valid JSON. If your ESD policy wasn't applied, check your JSON.

Agent Process
`````````````

During startup, the F5 LBaaSv2 agent reads all JSON files in :file:`/etc/neutron/services/f5/esd/` and evaluates the ESD as follows:

#. The JSON is valid (the agent ignores all invalid JSON files).
#. The :ref:`supported tag <esd-supported-tags>` definitions are formatted correctly:

    #. Use a single string, or a comma-delimited list using standard JSON list notation (``[]``) . [1]_
    #. The tag value (`profile`_, `policy`_, or `iRule`_) must exist in the ``/Common`` partition.
    #. All of the desired profiles, policies, and/or iRules must be configured on your BIG-IP *before* you deploy the ESD.

.. important::

    **The agent ignores all incorrectly-formatted tags**, including those referencing non-existent BIG-IP objects.
    If an ESD contains a mix of valid and invalid tags, the agent applies the valid tags and ignores the invalid ones.

.. [1] The ``lbaas_irule`` and ``lbaas_policy`` tags accept a comma-delimited list; all others accept only a single string.


Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device service cluster`.
- Operational OpenStack cloud (|openstack| release).
- F5 :ref:`agent <Install the F5 Agent>` and :ref:`LBaaSv2 driver <Install the F5 LBaaSv2 Driver>` installed on the hosts from which you want to manage your BIG-IP(s).
- Basic understanding of `BIG-IP system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.
- Basic understanding of `BIG-IP Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_.

Caveats
-------
L7 policies originated in the Mitaka release of OpenStack; as such:

- ESDs are available in a Mitaka (v9.x.x) or greater version of the F5 LBaaSv2 agent.
- ESDs are not available in the Liberty version of the F5 agent (v8.x.x).

Configuration
-------------

Enhanced Service Definitions (ESDs) must be defined in valid JSON. To apply multiple ESDs to a single application, define them all in a single file. Create as many individual ESDs as you need for your applications. Each ESD must have a unique name to avoid conflicts; if you give multiple ESDs the same name, the agent will implement one of them (method of selection is undefined).

Finally, restart the agent whenever you add or modify ESD files.

.. _esd-supported-tags:

Supported Tags
``````````````

Use the tags in the table below to define the policies you want the F5 agent to apply to the BIG-IP.

.. table:: Enhanced Service Definition tags

    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | Tag                        | Description                                                                                                                                                                                                                     | Example Value             |
    +============================+=================================================================================================================================================================================================================================+===========================+
    | lbaas\_ctcp                | Specify a named TCP profile for clients. This tag has a single value.                                                                                                                                                           | tcp-mobile-optimized      |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_stcp                | Specify a named TCP profile for servers. This tag has a single value.                                                                                                                                                           | tcp-lan-optimized         |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_cssl\_profile       | Specify a named client SSL profile to implement SSL/TLS offload. This can replace the use of, or override the life-cycle management of certificates and keys in LBaaSv2 SSL termination support. This tag has a single value.   | clientssl                 |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_sssl\_profile       | Specify a named server side SSL profile for re-encryption of traffic towards the pool member servers. **This tag can only be used once per ESD**.                                                                               | serverssl                 |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_irule (multiple)    | Specify a named iRule to attach to the virtual server. This tag can have multiple values, defined in a JSON list (``[]``). Any iRule priority must be defined within the iRule itself.                                          | [                         |
    |                            |                                                                                                                                                                                                                                 | "base\_sorry\_page",      |
    |                            |                                                                                                                                                                                                                                 | "base\_80\_443\_redirect" |
    |                            |                                                                                                                                                                                                                                 | ]                         |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_policy (multiple)   | Specify a named policy to attach to the virtual server. This tag can have multiple values, defined in a JSON list (``[]``). Any policy priority must be defined within the iRule itself.                                        | policy\_asm\_app1         |
    |                            | *All L7 content policies are applied before these policies.*                                                                                                                                                                    |                           |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_persist             | Specify a named fallback persistence profile for a virtual server. This tag has a single value.                                                                                                                                 | hash                      |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
    | lbaas\_fallback\_persist   | Specify a named fallback persistence profile for a virtual server. This tag has a single value.                                                                                                                                 | source\_addr              |
    +----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+

.. rubric:: Example

.. code-block:: JSON
    :caption: Basic ESD format

    {
      "<ESD name>": {
        "<tag_name>": "<tag value>",
        "<tag_name>": "<tag value>",
        …
      },
      …
    }

.. _esd-create:

Create an Enhanced Service Definition
-------------------------------------

#. Define the desired BIG-IP virtual server configurations in valid JSON.

    .. tip::

        The agent package includes an example ESD file, demo.json. You can amend this example file -- and save it with a unique name -- to create ESDs specific to your applications.


    .. code-block:: JSON
        :caption: demo.json

        {
          "esd_demo_1": {
            "lbaas_ctcp": "tcp-mobile-optimized",
            "lbaas_stcp": "tcp-lan-optimized",
            "lbaas_cssl_profile": "clientssl",
            "lbaas_sssl_profile": "serverssl",
            "lbaas_irule": ["_sys_https_redirect"],
            "lbaas_policy": ["demo_policy"],
            "lbaas_persist": "hash",
            "lbaas_fallback_persist": "source_addr"
          },
          "esd_demo_2": {
            "lbaas_irule": [
              "_sys_https_redirect",
              "_sys_APM_ExchangeSupport_helper"
            ]
          }
        }


#. Copy the ESD file(s) to the :file:`/etc/neutron/services/f5/esd/` directory.

#. Restart the F5 OpenStack agent.

    .. code-block:: bash

        $ sudo systemctl restart f5-openstack-agent


.. _esd-delete:

Delete an Enhanced Service Definition
-------------------------------------

Use Neutron's `L7 policy delete`_ operation to remove its associated ESD.

.. code-block:: bash

    $ neutron lbaas-l7policy-delete <ESD name or L7 policy ID>


.. _esd-usage:

Usage
-----

1. Configure all desired `profiles`_, `policies`_, and `iRules`_ on your BIG-IP.

2. :ref:`Create an ESD <esd-create>` (for example, :file:`/etc/neutron/services/f5/esd/my_esd.json`).

3. Restart the F5 OpenStack agent.

4. `Create a Neutron load balancer`_ with a listener (and pool, members, monitor).

5. `Create a Neutron L7 policy`_ object with a name parameter that matches your ESD name.

    .. code-block:: bash

        $ neutron lbaas-l7policy-create --listener <name or ID> --name <ESD name> --action <action>


    .. important::

        Neutron requires the ``--action`` parameter for ``lbaas-l7policy-create`` commands. The F5 OpenStack agent ignores ``--action`` when launching an ESD.

        .. rubric:: For example:

        .. code-block:: bash

            $ neutron lbaas-l7policy-create --listener vip1 --name mobile_app --action REJECT

        When the F5 agent receives the ``lbaas-l7policy-create`` command:

        - It looks up the ESD name ``mobile_app`` in its table of ESDs.
        - The agent applies each tag defined in the ``mobile_app`` ESD to the virtual server created for the listener named “vip1”.
        - The agent ignores the REJECT action.



Usage Examples
--------------

Following are examples of using ESDs to work around the limitations of LBaaSv2.

Add iRules
``````````

Use the ``lbaas_irule`` tag to add any desired `iRules`_ to any BIG-IP virtual server associated with an LBaaSv2 load balancer.

For example, if you want to re-write certificate values into request headers:

#. Create the desired iRule(s) in the ``/Common`` partition on the BIG-IP.
#. Define the ``lbaas_irule`` tag with a JSON list.

.. rubric:: Example:

.. code-block:: JSON
    :linenos:

    {
      "esd_demo_1": {
        \\ define a single iRule
        "lbaas_irule": ["header_rewrite"]
      },
      "esd_demo_2": {
        \\ define two (2) iRules
        "lbaas_irule": [
          "header_rewrite",
          "remove_response_header"
        ]
      }
    }

.. important::

    When using iRules, be sure to define the iRule priority within the iRule itself. The order in which the F5 agent applies iRules isn't guaranteed; the agent adds iRules in the order in which they're defined in the ESD.


Add LTM Policies
````````````````

Use the ``lbaas_policy`` tag to assign a BIG-IP LTM `policy`_ to a virtual server associated with an LBaaSv2 load balancer.

#. Create the `policy`_ in the ``/Common`` partition on the BIG-IP.
#. Define the ``lbaas_policy`` tag with a JSON list.

.. rubric:: Example:

.. code-block:: JSON
    :linenos:

    {
      \\ define a single policy
      "esd_demo_1": {
        "lbaas_policy": ["custom_policy1"]
      },
      \\ define two (2) policies
      "esd_demo_2": {
        "lbaas_policy ": [
        "custom_policy1",
        "custom_policy2"
        ]
      }
    }


Add Server-side SSL Termination
```````````````````````````````

Use the ``lbaas_sssl_profile`` tag to add `BIG-IP server-side SSL termination`_ to a virtual server associated with an LBaaSv2 load balancer.

.. rubric:: Example:

.. code-block:: JSON

    "lbaas_sssl_profile": "serverssl"


Customize Client-side SSL Termination
`````````````````````````````````````

Use the ``lbaas_cssl_profile tag`` tag to add a `BIG-IP SSL profile`_ to a virtual server associated with an LBaaSv2 load balancer.

#. Create a `client SSL profile`_ in the ``/Common`` partition on the BIG-IP.
#. `Create an LBaaSv2 HTTPS listener`_.
#. Create an L7 policy object using the ``lbaas_cssl_profile`` tag.

.. rubric:: Example:

.. code-block:: JSON

    "lbaas_cssl_profile": "clientssl"


Customize Session Persistence
`````````````````````````````

Use the ``lbaas_persist`` and ``lbaas_fallback_persist`` tags to configure a `BIG-IP session persistence profile`_ on a virtual server associated with an LBaaSv2 load balancer.


.. important::

    In the LBaaSv2 session persistence model, persistence types apply to pools, not listeners. The F5 agent maps LBaaSv2 pool session persistence values to the BIG-IP virtual server(s) associated with the pool. The BIG-IP provides many persistence profiles beyond those available in LBaaSv2, including ``dest_addr``, ``hash``, ``ssl``, ``sip``, etc.

.. rubric:: Example:

.. code-block:: JSON
    :linenos:

    "lbaas_persist": "hash",
    "lbaas_fallback_persist": "source_addr"

.. tip::

    It's good practice to define a fallback persistence profile as well, in case a client doesn't support the specified persistence profile.


Use TCP Profiles
````````````````

Use the ``lbaas_ctcp`` tag to define a `BIG-IP TCP profile`_ for a virtual server associated with an LBaaSv2 load balancer. BIG-IP TCP profiles, which determine how a server processes TCP traffic, can fine-tune TCP performance for specific applications.

- ``lbaas_ctcp`` -- Use this tag for client profiles.
- ``lbaas_stcp`` -- Use this tag for server profiles.

.. important::

    If you only define the client tag (``lbaas_ctcp``), the F5 agent assigns the client profile to the virtual server for both client- and server-side traffic.

.. rubric:: For example:

If your load balancer fronts an application used for mobile clients, you can use the ``tcp_mobile_optimized`` BIG-IP client SSL profile to optimize TCP processing.

.. code-block:: json

    "lbaas_ctcp": "tcp_mobile_optimized"

Of course, that profile may not be optimal for traffic between your BIG-IP and the pool member servers. You can specify different profiles for client-side and server-side traffic.

For ``esd_demo_1`` in the example below, we define a single TCP profile ("tcp") for both client- and server-side traffic. For ``esd_demo_2``, we assign separate TCP policies for client- and server-side traffic (``tcp_mobile_optimized`` and ``tcp_lan_optimized``, respectively).

.. code-block:: json
    :linenos:

    {
      "esd_demo_1": {
      "lbaas_ctcp": "tcp"
      },
      "esd_demo_2": {
        "lbaas_ctcp": "tcp_mobile_optimized",
        "lbaas_stcp": "tcp_lan_optimized"
      }
    }



.. _L7 policy: https://wiki.openstack.org/wiki/Neutron/LBaaS/l7#L7_Policies
.. _Create a Neutron load balancer: https://docs.openstack.org/mitaka/networking-guide/config-lbaas.html#building-an-lbaas-v2-load-balancer
.. _Create a Neutron L7 policy: https://docs.openstack.org/cli-reference/neutron.html
.. _iRules: https://devcentral.f5.com/irules
.. _policies: https://support.f5.com/csp/article/K15085
.. _profiles: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-profiles-reference-12-0-0/2.html
.. _profile: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-profiles-reference-12-0-0/2.html
.. _policy: https://support.f5.com/csp/article/K15085
.. _iRule: https://devcentral.f5.com/irules
.. _client SSL profile: https://support.f5.com/csp/article/K14783
.. _BIG-IP server-side SSL termination: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-ssl-administration-13-0-0/4.html#guid-45595e00-5179-4055-87f7-277eb7d922bd
.. _BIG-IP SSL profile: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-profiles-reference-13-0-0/6.html
.. _Create an LBaaSv2 HTTPS listener: https://docs.openstack.org/mitaka/networking-guide/config-lbaas.html#adding-an-https-listener
.. _BIG-IP session persistence profile: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-profiles-reference-13-0-0/4.html
.. _BIG-IP TCP profile: https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-profiles-reference-13-0-0/1.html#guid-4b08badd-ccd9-4ddc-a4c3-1d8f788f38c3
.. _L7 policy delete: https://docs.openstack.org/cli-reference/neutron.html#neutron-lbaas-l7policy-delete
