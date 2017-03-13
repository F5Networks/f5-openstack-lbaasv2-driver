Customizing OpenStack LBaaSv2 Using Enhanced Service Definitions
=================================================================

There are many load balancing configurations which have no direct
implementation in the OpenStack LBaaSv2 specification. It is easy to
directly customize BIG-IP traffic management using profiles, policies,
and iRules, but LBaaSv2 has no way to apply these to BIG-IP virtual
servers. To help users get the most from their BIG-IPs, F5 Networks
extended its implementation of LBaaSv2 to add an Enhanced Service
Definition (ESD) feature. With ESDs, you can deploy OpenStack load
balancers customized for specific applications.

How ESDs Work
-------------

An ESD is a set of tags and values that define custom settings,
typically one or more profiles, policies, or iRules which are applied to
a BIG-IP virtual server. ESDs are stored in JSON files on the system
running an F5 OpenStack LBaaSv2 agent. When the agent starts, it reads
all ESD JSON files located in /etc/neutron/services/f5/esd/, ignoring
files that are not valid JSON. A JSON file can contain multiple ESDs,
and each ESD contains a set of predefined tags and values. The agent
validates each tag and discards invalid tags. ESDs remain fixed in agent
memory until an agent is restarted.

You apply ESDs to virtual servers using LBaaSv2 L7 policy operations.
When you create an LBaaSv2 L7 policy object, the agent checks if the
policy name matches the name of an ESD. If it does, the agent applies
the ESD to the virtual server associated with the policy. If the policy
name does not match an ESD name, a standard L7 policy is created
instead. Essentially, the F5 agent overloads the meaning of an L7 policy
name. If an L7 policy name matches an ESD name, creating an L7 policy
means “apply an ESD.” If an L7 policy name does not match an ESD name,
creating an L7 policy means “create an L7 policy.”

While you can apply multiple L7 policies, doing so will overwrite
virtual server settings defined by previous ESDs. Deleting an L7 policy
that matches an ESD will remove all ESD settings from the virtual
server, and return the virtual server to its original state. For these
reasons, it is best to define a single ESD that contains all settings
you want to apply for a specific application, instead of applying
multiple ESDs.

Because L7 policies were introduced in the Mitaka release of OpenStack,
you can only use ESDs with a Mitaka (or greater) version of the F5
LBaaSv2 agent. You cannot use ESDs with the Liberty version of the F5
agent. Release v9.3.0 is the first version of the agent that supports
ESDs.

Creating ESDs
-------------

Create ESDs by editing files to define one or more ESDs in JSON format.
Each file can contain any number of ESDs, and you can create any number
of ESD files. Files can have any valid file name, but must end with a
“.json” extension (e.g., mobile\_app.json). Copy the ESD files to the
/etc/neutron/services/f5/esd/ directory. ESDs must have a unique name
across all files. If you define more than one ESD using the same name,
the agent will retain one of the ESDs, but which one is undefined.
Finally, restart the agent whenever you add or modify ESD files.

ESD files have this general format::

  {
    "<ESD name>": {
      "<tag_name>": "<tag value>",
      "<tag_name>": "<tag value>",
      …
    },
    …
  }

An example ESD file, demo.json, is installed with the agent and provides
examples you can follow::

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

ESD files must be formatted as valid JSON. If your file is not valid
JSON, all ESDs in the file will be ignored. Consider using a JSON lint
application (e.g., jsonlint.com) to validate your JSON files.

The following tags are supported for ESDs:

+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| Tag                        | Description                                                                                                                                                                                                                     | Example                   |
+============================+=================================================================================================================================================================================================================================+===========================+
| lbaas\_ctcp                | Specify a named TCP profile for clients. This tag has a single value.                                                                                                                                                           | tcp-mobile-optimized      |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_stcp                | Specify a named TCP profile for servers. This tag has a single value.                                                                                                                                                           | tcp-lan-optimized         |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_cssl\_profile       | Specify a named client SSL profile to implement SSL/TLS offload. This can replace the use of, or override the life-cycle management of certificates and keys in LBaaSv2 SSL termination support. This tag has a single value.   | clientssl                 |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_sssl\_profile       | Specify a named server side SSL profile for re-encryption of traffic towards the pool member servers. This tag should only be present once.                                                                                     | serverssl                 |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_irule (multiple)    | Specify a named iRule to attach to the virtual server. This tag can have multiple values. Any iRule priority must be defined within the iRule itself.                                                                           | base\_sorry\_page,        |
|                            |                                                                                                                                                                                                                                 |                           |
|                            |                                                                                                                                                                                                                                 | base\_80\_443\_redirect   |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_policy (multiple)   | Specify a named policy to attach to the virtual server. This tag can have multiple values Any policy priority must be defined within the iRule itself. All L7 content policies are applied first, then these named policies.    | policy\_asm\_app1         |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_persist             | Specify a named fallback persistence profile for a virtual server. This tag has a single value.                                                                                                                                 | hash                      |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+
| lbaas\_fallback\_persist   | Specify a named fallback persistence profile for a virtual server. This tag has a single value.                                                                                                                                 | source\_addr              |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+

An ESD does not need to include every tag. Only included tags will be
applied to a virtual server.

During startup, the F5 LBaaSv2 agent will read all ESD JSON files (any
file with .json extension) and validate the ESD by ensuring:

1. The ESD file is a valid JSON format. Any invalid JSON file will be
   ignored.
2. The tag name is valid (i.e., one of the tags listed in the table
   above).
3. The tag value is correctly defined: a single string (for most tags),
   or a comma delimited list using JSON [] notation (only for
   lbaas\_irule and lbaas\_policy tags).
4. The tag value (profile, policy, or iRule) exists in the Common
   partition. Keep these rules in mind:
   a. Any profile, policy, or iRule used in an ESD must be created in
      the Common partition.
   b. Any profile, policy, or iRule must be pre-configured on your
      BIG-IP before re-starting the F5 LBaaSv2 agent.

Any tag that does not pass the validation steps above will be ignored.
An ESD that contains a mix of valid and invalid tags will still be used,
but only valid tags will be applied.

Using ESDs
----------

Follow this workflow for using ESDs.

1. Pre-configure profiles, policies, and iRules on your BIG-IP.
2. Create an ESD in a JSON file located in
   /etc/neutron/services/f5/esd/.
3. Restart the F5 LBaaSv2 agent.
4. Create a Neutron load balancer with a listener (and pool, members,
   monitor).
5. Create a Neutron L7 policy object with a name parameter that matches
   your ESD name.

You apply an ESD to a virtual server using L7 policy objects in LBaaSv2.
Using the Neutron CLI, you can create an L7 policy like this::

  lbaas-l7policy-create --listener <name or ID> --name <ESD name> --action <action>

The action parameter is ignored, but must be included for Neutron to
accept the command. For example::

  lbaas-l7policy-create --listener vip1 --name mobile_app --action REJECT

In this example, when the F5 agent receives the lbaas-l7policy-create
command, it looks up the ESD name “mobile\_app” in its table of ESDs.
The agent applies each tag defined in the ESD named “mobile\_app” to the
virtual server created for the listener named “vip1”. The REJECT action
is ignored.

Use the L7 policy delete operation to remove an ESD::

  lbaas-l7policy-delete <ESD name or L7 policy ID>

It is important to note that ESDs will overwrite any existing setting of
a BIG-IP virtual server. For example, if you create an LBaaSv2 pool with
cookie session persistence (which is applied to the virtual server
fronting the pool) and then apply an ESD that uses hash persistence,
cookie persistence will be replaced with hash persistence. Removing the
ESD by deleting the L7 policy will restore the virtual server back to
cookie persistence. Likewise, creating a pool with session persistence
*after* applying an ESD will overwrite the ESD persist value, if
defined. Order of operations is important – last one wins.

Use Cases
---------

Following are examples of using ESDs to work around the limitations of
LBaaSv2.

Customizing Client-side SSL Termination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LBaaSv2 supports client-side SSL termination by creating TLS listeners –
listeners with TERMINATED\_HTTPS protocol. Using TERMINATED\_HTTPS in
LBaaSv2 requires a certificate and key stored in the Barbican secret
store service. While this satisfies many security requirements, you may
want to use an SSL profile different from what is created with a
Barbican certificate and key.

To use a different profile, create a listener with an HTTPS protocol,
and then create an L7 policy object using an ESD that has an
lbaas_cssl_profile tag. For example::

  "lbaas_cssl_profile": "clientssl"

Adding Server-side SSL Termination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LBaaSv2 has no way of specifying server-side SSL termination, as TLS
listeners only define a client-side SSL profile. You may need to also
re-encrypt traffic between your BIG-IP and pool member servers. To add
server-side SSL termination, use an ESD that includes an
lbaas_sssl_profile tag. For example::

  "lbaas_sssl_profile": "serverssl"

Customizing Session Persistence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LBaaSv2 supports session persistence, though in the LBaaSv2 model
persistence types are defined for pools not listeners. The F5 agent maps
LBaaSv2 pool session persistence values to BIG-IP virtual servers
associated with the pool. LBaaSv2 only supports three options
(HTTP_COOKIE, APP_COOKIE, and SOURCE_ADDR), and these are mapped to
either cookie or source\_addr persistence on BIG-IPs. Many more
persistence profiles are available on BIG-IPs, such as dest_addr, hash,
ssl, sip, etc. To use these profiles, specify the lbaas_persist and
lbaas_fallback_persist tags in an ESD. For example::

  "lbaas_persist": "hash",
   "lbaas_fallback_persist": "source_addr"

It is good practice to define a fallback persistence profile as well in
case a client does not support the persistence profile you specify.

Adding iRules
~~~~~~~~~~~~~

iRules are a powerful tool for customizing traffic management. As an
example, you may want to re-write certificate values into request
headers. Create an iRule that does this and use the tag lbaas\_irule to
add the iRule to a virtual server. Unlike other tags (except
lbaas\_policy), the lbaas\_irule tag supports multiple values. You
define values for lbaas\_irule using JSON list notation (comma delimited
strings within brackets, []). Use brackets [] even if you only define a
single iRule. Here are two examples: one ESD applies a single iRule, the
other applies two iRules::

  {
    "esd_demo_1": {
      "lbaas_irule": ["header_rewrite"]
    },
    "esd_demo_2": {
      "lbaas_irule": [
      "header_rewrite",
      "remove_response_header"
     ]
    }
  }

When using iRules, be sure to define the iRule priority within the iRule
itself. The order of application of iRules is not guaranteed, though the
agent makes a best effort by adding iRules in the order they are defined
in the tag.

Adding Policies
~~~~~~~~~~~~~~~

The Mitaka release of OpenStack LBaaSv2 introduced L7 policies to manage
traffic based on L7 content. The LBaaSv2 L7 policy and rule model may
work for your needs. If not, create a policy on your BIG-IP and apply
that policy to your LBaaSv2 listener using the lbaas\_policy tag. As
with the lbaas\_irule tag, the lbaas\_policy tag requires brackets
surrounding one or more policy names. For example::

  {
    "esd_demo_1": {
      "lbaas_policy": ["custom_policy1"]
    },
    "esd_demo_2": {
      "lbaas_policy ": [
      "custom_policy1",
      "custom_policy2"
      ]
    }
  }

Using TCP Profiles
~~~~~~~~~~~~~~~~~~

ESDs allow you to define TCP profiles that determine how a server
processes TCP traffic. These can be used to fine tune TCP performance
for specific applications. For example, if your load balancer fronts an
application used for mobile clients, you can use the
‘tcp\_mobile\_optimized’ client profile to optimize TCP processing. Of
course, that profile may not be optimal for traffic between your BIG-IP
and the pool member servers, so you can specify different profiles for
client-side and server-side traffic. Use the lbaas\_ctcp tag for client
profiles and the lbaas\_stcp tag for server profiles. If you only
include the client tag, lbaas\_ctcp, and not the server tag,
lbaas\_stcp, the client profile is used for both. Following are two
examples. In the first, esd\_demo\_1, the tcp profile will be used for
both client-side and server-side traffic. In the second, esd\_demo\_2,
the tcp\_mobile\_optimized profile is used for client-side traffic, and
tcp\_lan\_optimized profile is used for server-side traffic::

  {
    "esd_demo_1": {
    "lbaas_ctcp": "tcp"
    },
    "esd_demo_2": {
      "lbaas_ctcp": "tcp_mobile_optimized",
      "lbaas_stcp": "tcp_lan_optimized"
    }
  }

Helpful Hints
~~~~~~~~~~~~~

1. Use a JSON lint application to validate your ESD files. Forgetting a
   quote, including a trailing comma, or not balancing braces/brackets
   are common mistakes that cause JSON validation errors.

2. Restart the F5 LBaaSv2 agent (f5-openstack-agent) after adding or
   modifying ESD files.

3. Use a unique name for each ESD you define. ESD names are case
   sensitive.

4. Any profile, policy, or iRule referenced in your ESD must be
   pre-configured on your BIG-IP, and it must be created in the Common
   partition.

5. ESDs overwrite any existing settings. For example, the
   lbaas\_cssl\_profile replaces the SSL profile created for TLS
   listeners.

6. When using iRules and policies, remember that any iRule priority must
   be defined within the iRule itself.

7. If DEBUG logging is enabled, check the agent log,
   /var/log/neutron/f5-openstack-agent.log, for statements that report
   whether a tag is valid or invalid.
