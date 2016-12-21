F5 LBaaSv2 L7 Content Switching
===============================

Overview
--------

L7 content switching takes its name from layer 7 of the OSI Model, also called the application layer. [#f1]_ As the name implies, L7 content switching decisions are based on the application data, or content, of request traffic as it passes through the virtual server. Via the API, you can define actions to be taken when certain content conditions are met. See the OpenStack Neutron `LBaaS Layer 7 rules documentation <http://specs.openstack.org/openstack/neutron-specs/specs/mitaka/lbaas-l7-rules.html>`_ for more information.

.. [#f1] https://wiki.openstack.org/wiki/Neutron/LBaaS/l7 

Neutron LBaaSv2 API L7 Policies and Rules
`````````````````````````````````````````

In Neutron an L7 Policy is a collection of L7 rules associated with a Listener; it may also have an association to a back-end pool. Policies describe actions that should be taken by the load balancing software if all of the rules in the policy return true or match.

Policy Actions:

    Valid L7 policy actions are one of:

        REJECT – The request is blocked and a TCP connection reset is sent to the client. The HTTP request is not forwarded to a backend pool.

        REDIRECT_TO_POOL – The request is forwarded to a member in the redirect pool.

        REDIRECT_TO_URL – The request is forward to the URL specified in the redirect URL.

Policy Rule Type:

    An L7 Rule is a single, simple logical test that returns either true or false. An L7 rule has a type, a comparison type, a value, and an optional key that is used for certain rule types. Valid rule types are defined by the following operands:

        HOST_NAME – The rule does a comparison to the hostname in the HTTP ‘Host’ header with the specified value parameter.

        PATH – The rule compares the HTTP URI path to the specified value parameter

        FILE_TYPE – The rule compares the file extension of the HTTP URI with the specified rule value (e.g. ‘pdf’, ‘jpg’, etc.

        HEADER -- The rule compares an HTTP header in the request, as specified by the key parameter, with the value specified in the rule.

        COOKIE – The rule searches for the cookie, as specified by the key parameter, and compares it to the rule’s value.

Policy Rule Comparison Type:

    In addition to a rule type there are five comparison types that are applied to the rule’s operand and compared with the rule value to determine if a match exists.

        STARTS_WITH – operand starts with string

        ENDS_WITH – operand ends with string

        EQUAL_TO – operand matches the string

        CONTAINS – operand contains a substring value

        REGEX – operand matches the provided regular expression. **(currently not supported)**

Neutron Policy Logic:

All the rules in an L7 policy must match before the associated action is executed. So if a policy has a set of rules: R1, R2, … Rn, and an action, A, then the following logic holds:

    If (R1 and R2 and … Rn ) then A

Policy rules can also be negated by using the –invert parameter when specifying the rules. For example, the comparison type, EQUAL_TO can be transformed to NOT_EQUAL_TO, by specifying –invert.

L7 policies are ranked by a position value and are evaluated according to their rank. The first policy that evaluates to true is executed and all subsequent policies are skipped. Given a set of n policies, where policy Pn has a rank n and an action An, the following logic holds:

    If (P1) then A1

    Else if (P2) then A2

    …

    Else if (Pn) then An

    Else:

    Send request to default pool

OpenStack Policy/Rules Definition Versus BIG-IP® Policy/Rules:
``````````````````````````````````````````````````````````````

The Neutron L7 terminology does not directly align with the common vocabulary of BIG-IP Local Traffic Manager. In the BIG-IP LTM, policies also have a set of rules, but it is the rules that specify actions and not the policy. Also, policies attached to a virtual server on the BIG-IP are all evaluated regardless of the truth of the associated rules. In addition to this difference the BIG-IP policies have no ordinal, it is the BIG-IP rules that have this attribute. Because of these confusing differences it is useful to attempt to define the terms as they apply to each domain.

    +------------------+-------------------------------+
    | Neutron LBaaS L7 | BIG-IP® Local Traffic Manager |
    +==================+===============================+
    | Policy           | Policy Rules (wrapper_policy) |
    +------------------+-------------------------------+
    | Policy Action    | Rule Action                   |
    +------------------+-------------------------------+
    | Policy Position  | Rule Ordinal                  |
    +------------------+-------------------------------+
    | Rule             | Rule Conditions               |
    +------------------+-------------------------------+


The BIG-IP LTM policy has a name, description, a set of rules, and a strategy on how those rules are evaluated. In fact, L7 policies in OpenStack are more akin to a collection BIG-IP LTM policy rules that are evaluated with the ‘First match’ strategy.

The BIG-IP LTM rules have conditions, actions, and an ordinal and would need to be created based on the L7 policy and rule attributes.

Neutron LBaaSv2 API L7 Rules Implementation:

    A combination of L7Policy and L7Rule elements will be mapped to TMOS traffic policies and in the case of specific L7Rule compare_types, iRules.

    The major reasons to implement LBaaS L7 Rules in TMOS traffic policies, instead of a pure iRule implementation, are:

        Performance, all L7 Rule types map directly to TMOS traffic policy match conditions:

            +--------------+-------------------------------------+
            | L7 Rule Type | TMOS Traffic Policy Match Condition |
            +==============+=====================================+
            | Hostname     | HTTP Host                           |
            +--------------+-------------------------------------+
            | Path         | HTTP URI + path                     |
            +--------------+-------------------------------------+
            | FileType     | HTTP URI + extension                |
            +--------------+-------------------------------------+
            | Header       | HTTP Header                         |
            +--------------+-------------------------------------+
            | Cookie       | HTTP Cookie                         |
            +--------------+-------------------------------------+

        The LBaaS L7 Rules requirement that ‘the first L7Policy that returns a match will be executed’ directly maps to TMOS traffic policy execution strategy ‘first-match’.

        Four of the five L7Rule compare_type values directly map to TMOS traffic policy rule conditions:

            +----------------------+-------------------------+------------------------------------------+
            | L7 Rule Compare Type | L7 '--invert' Specified | TMOS Traffic Policy Rule Match Condition |
            +======================+=========================+==========================================+
            | STARTS_WITH          | No                      | Begins with                              |
            +----------------------+-------------------------+------------------------------------------+
            | STARTS_WITH          | Yes                     | Does not begin with                      |
            +----------------------+-------------------------+------------------------------------------+
            | ENDS_WITH            | No                      | Ends with                                |
            +----------------------+-------------------------+------------------------------------------+
            | ENDS_WITH            | Yes                     | Does not end with                        |
            +----------------------+-------------------------+------------------------------------------+
            | EQUAL_TO             | No                      | Is                                       |
            +----------------------+-------------------------+------------------------------------------+
            | EQUAL_TO             | Yes                     | Is not                                   |
            +----------------------+-------------------------+------------------------------------------+
            | CONTAINS             | No                      | Contains                                 |
            +----------------------+-------------------------+------------------------------------------+
            | CONTAINS             | Yes                     | Does not contain                         |
            +----------------------+-------------------------+------------------------------------------+
            | REGEX                | X                       | No direct mapping                        |
            +----------------------+-------------------------+------------------------------------------+

        All L7Policy actions map directly to TMOS traffic policy rule actions:

            +------------------+---------------------------------+
            | L7 Policy Action | TMOS Traffic Policy Rule Action |
            +==================+=================================+
            | Reject           | Reset traffic                   |
            +------------------+---------------------------------+
            | RedirectToUrl    | Redirect                        |
            +------------------+---------------------------------+
            | RedirectToPool   | Forward traffic to pool         |
            +------------------+---------------------------------+

Prerequisites
-------------

- Licensed, operational BIG-IP :term:`device` or :term:`device cluster`.
- Operational OpenStack cloud (|openstack| release).
- Administrator access to both BIG-IP device(s) and OpenStack cloud.
- F5 :ref:`agent <agent:home>` and :ref:`service provider driver <Install the F5 LBaaSv2 Driver>` installed on the Neutron controller and all other hosts from which you want to provision LBaaS services.
- Knowledge of `OpenStack Networking <http://docs.openstack.org/mitaka/networking-guide/>`_ concepts.
- Basic understanding of `BIG-IP system configuration <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/bigip-system-initial-configuration-12-0-0/2.html#conceptid>`_.
- Basic understanding of `BIG-IP Local Traffic Management <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/ltm-basics-12-0-0.html>`_

Caveats
-------

- The REGEX comparison type is not supported in this release.

Configuration
-------------

#. It's not necessary to make any agent configuration changes. Rather, L7 switching policy and rule definitions are made when creating or updating a listener, as shown in the example below from the OpenStack documentation.

#. CLI Example (copied from the Neutron L7 feature page linked above):

    .. code-block:: text
        :emphasize-lines: 2,4,6,11,13

        # Create a listener
        neutron lbaas-create-listener listener1
        # Create a pool
        neutron lbaas-create-pool pool1
        # Create a policy
        neutron --policy policy1 lbaas-create-l7policy --name "policy1" --listener "listener1" --action redirect_to_pool --pool "pool1" --position 1
        # Create a rule for this policy
        # Once the below operation has completed, a new policy will exist on the device called 'wrapper_policy'.
        # It will have a single rule called redirect_to_pool_1.
        # A single condition and a single action will exist.
        neutron lbaas-create-l7rule rule1 --rule-type path --compare-type contains --value "i_t" --policy policy1
        # Create a second rule for the above policy
        neutron lbaas-create-l7rule rule2 --rule-type cookie --compare-type ends_with --key "cky" --value "i" --invert --policy policy1

    .. code-block:: text

        # The resulting BIG-IP® LTM Policy configuration from the steps above.
        ltm policy wrapper_policy {
            controls { forwarding }
            last-modified 2016-12-05:09:19:05
            partition Project_9065d69e806a4b4894a47fed7484a006
            requires { http }
            rules {
                reject_1 {
                    actions {
                        0 {
                            forward
                            reset
                        }
                    }
                    conditions {
                        0 {
                            http-uri
                            path
                            contains
                            values { i_t }
                        }
                        1 {
                            http-cookie
                            name cky
                            ends-with
                            values { i }
                        }
                    }
                    ordinal 1
                }
            }
            status legacy
            strategy /Common/first-match
        }

Further Reading
---------------

.. seealso:: See the links below for further reading.

    * OpenStack Neutron `LBaaS Layer 7 rules documentation <http://specs.openstack.org/openstack/neutron-specs/specs/mitaka/lbaas-l7-rules.html>`_
    * OpenStack Neutron `LBaaSv2 l7 Wiki <https://wiki.openstack.org/wiki/Neutron/LBaaS/l7>`_
    * `BIG-IP Local Traffic Management -- Getting Started with Policies <https://support.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/local-traffic-policies-getting-started-12-1-0.html?sr=59376207>`_
