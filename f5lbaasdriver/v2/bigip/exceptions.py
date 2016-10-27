# coding=utf-8
u"""F5 Networks® LBaaSv2 Exceptions."""
# Copyright 2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from neutron_lib import exceptions as q_exc


class F5LBaaSv2DriverException(q_exc.NeutronException):
    """General F5 LBaaSv2 Driver Exception."""

    message = "F5LBaaSv2DriverException"

    def __init__(self, message=None):
        if message:
            self.message = message


class F5MismatchedTenants(F5LBaaSv2DriverException):
    """The loadbalancer tenant is not the same as the network tenant."""

    message = "Tenant Id of network and loadbalancer mismatched"

    def __str__(self):
        return self.message


class F5DeleteListenerWithAttachedPool(F5LBaaSv2DriverException):
    """The listener cannot become unbound from the pool."""

    message = "Cannot delete listener with an attached pool. " \
              "Delete pool first."


class PolicyHasMoreThanOneListener(F5LBaaSv2DriverException):
    """A policy should have only one listener."""

    def __str__(self):
        return self.message


class RuleHasMoreThanOnePolicy(F5LBaaSv2DriverException):
    """A rule should have only one policy."""
    pass
