# coding=utf-8
# Copyright 2022 F5 Networks Inc.
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

from oslo_log import log as logging

from neutron.services.network_ip_availability import plugin as niap

from neutron_lbaas.extensions import lbaas_agentschedulerv2

from neutron_lib import exceptions as n_exc

from f5lbaasdriver.v2.bigip import constants_v2

LOG = logging.getLogger(__name__)


class ValidationError(lbaas_agentschedulerv2.NoEligibleLbaasAgent):
    message = "Validation error for loadbalancer %(loadbalancer_id)s."


class Validator(object):
    pass


class LoadBalancerValidator(Validator):

    def __init__(self):
        super(LoadBalancerValidator, self).__init__()

    def validate_create(self, context, lb):
        pass

    def validate_update(self, context, old_lb, lb):
        pass


class InvalidFlavor(ValidationError):
    message = "Invalid flavor %(flavor)s for %(loadbalancer_id)s."


class FlavorValidator(LoadBalancerValidator):

    def __init__(self):
        super(FlavorValidator, self).__init__()

    def validate(self, context, lb):
        f = lb.flavor
        if f < 1 or f > 13 or \
           (f > 8 and f < 11):
            raise InvalidFlavor(loadbalancer_id=lb.id, flavor=f)

    def validate_create(self, context, lb):
        self.validate(context, lb)

    def validate_update(self, context, old_lb, lb):
        self.validate(context, lb)


class NoAvailableSnatIPv4(ValidationError):
    message = ("No available v4 SNAT IP for %(loadbalancer_id)s. "
               "Required %(required)s, available %(available)s")


class NoAvailableSnatIPv6(ValidationError):
    message = ("No available v6 SNAT IP for %(loadbalancer_id)s. "
               "Required %(required)s, available %(available)s")


class SnatIPValidator(LoadBalancerValidator):

    def __init__(self, driver):
        super(SnatIPValidator, self).__init__()
        self.driver = driver

    def get_available_ips(self, context, lb):
        niap_plugin = niap.NetworkIPAvailabilityPlugin.get_instance()
        get_subnet = self.driver.plugin.db._core_plugin.get_subnet
        subnet = get_subnet(context, lb.vip_subnet_id)
        result = niap_plugin.get_network_ip_availability(context,
                                                         subnet["network_id"])

        if not result:
            # Impossible path
            raise n_exc.NetworkNotFound(net_id=id)

        # We need to assume that VIP network only has one v4 subnet
        # and one v6 subnet at most

        v4_a = None
        v6_a = None
        ipa = result["subnet_ip_availability"]
        for i in ipa:
            if i["ip_version"] == 4:
                v4_a = i["total_ips"] - i["used_ips"]
            if i["ip_version"] == 6:
                v6_a = i["total_ips"] - i["used_ips"]

        return v4_a, v6_a

    def validate_create(self, context, lb):
        flavor = lb.flavor
        if flavor in [7, 8]:
            return

        snat_map = constants_v2.FLAVOR_SNAT_MAP
        v4_r = snat_map[4][flavor]
        v6_r = snat_map[6][flavor]

        v4_a, v6_a = self.get_available_ips(context, lb)

        if v4_a is not None and v4_a < v4_r:
            raise NoAvailableSnatIPv4(loadbalancer_id=lb.id, required=v4_r,
                                      available=v4_a)

        if v6_a is not None and v6_a < v6_r:
            raise NoAvailableSnatIPv6(loadbalancer_id=lb.id, required=v6_r,
                                      available=v6_a)

    def validate_update(self, context, old_lb, lb):
        flavor = lb.flavor
        if flavor in [7, 8]:
            return

        snat_map = constants_v2.FLAVOR_SNAT_MAP
        v4_r = snat_map[4][flavor]
        v6_r = snat_map[6][flavor]

        old_flavor = old_lb.flavor
        old_v4_r = snat_map[4][old_flavor]
        old_v6_r = snat_map[6][old_flavor]

        if old_flavor not in [7, 8]:
            v4_r -= old_v4_r
            v6_r -= old_v6_r

        v4_a, v6_a = self.get_available_ips(context, lb)

        if v4_a is not None and v4_r > 0 and v4_a < v4_r:
            raise NoAvailableSnatIPv4(loadbalancer_id=lb.id, required=v4_r,
                                      available=v4_a)

        if v6_a is not None and v6_r > 0 and v6_a < v6_r:
            raise NoAvailableSnatIPv6(loadbalancer_id=lb.id, required=v6_r,
                                      available=v6_a)
