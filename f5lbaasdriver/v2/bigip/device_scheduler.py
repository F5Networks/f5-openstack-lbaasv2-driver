# coding=utf-8
"""Schedule agent to bind to a load balancer."""
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

import ipaddress
import random
import sys

from oslo_log import log as logging
from oslo_utils import importutils

from neutron_lib import context as ncontext
from neutron_lib import exceptions as nexception

from neutron_lbaas import agent_scheduler
from neutron_lbaas.extensions import lbaas_agentschedulerv2

from neutron_lbaas_inventory.db.inventory_db import InventoryDbPlugin

from f5lbaasdriver.v2.bigip import agent_scheduler as f5_agent_scheduler
from f5lbaasdriver.v2.bigip import config
from f5lbaasdriver.v2.bigip import constants_v2

cfg = config.cfg
LOG = logging.getLogger(__name__)


class NoEligibleLbaasDevice(lbaas_agentschedulerv2.NoEligibleLbaasAgent):
    message = ("No eligible device found "
               "for loadbalancer %(loadbalancer_id)s.")


class NoActiveLbaasDevice(lbaas_agentschedulerv2.NoActiveLbaasAgent):
    message = ("No active device found "
               "for loadbalancer %(loadbalancer_id)s.")


class NoDedicatedLbaasDevice(NoActiveLbaasDevice):
    message = ("The dedicated devices specified by "
               "user-device-map does not exist.")


class LbaasDeviceDisappeared(nexception.Conflict):
    message = ("Device %(device_id)s for loadbalancer %(loadbalancer_id)s "
               "is disappeared.")


class LbaasDeviceDisabled(nexception.Conflict):
    message = ("Device %(device_id)s for loadbalancer %(loadbalancer_id)s "
               "is disabled.")


class BadDeviceInventory(lbaas_agentschedulerv2.NoActiveLbaasAgent):
    message = ("Fail to load device inventory: %(loadbalancer_id)s")


class DeviceSchedulerBusy(NoEligibleLbaasDevice):
    message = ("Device scheduler is busy and cannot schedule a device "
               "for loadbalancer %(loadbalancer_id)s.")


class DeviceSchedulerNG(object):
    """NextGen Device Scheduler for LBaaSv2"""

    def __init__(self):
        super(DeviceSchedulerNG, self).__init__()
        self.filters = []
        names = cfg.CONF.device_filters
        for name in names:
            filter_path = ".".join([DeviceSchedulerNG.__module__, name])
            self.filters.append(importutils.import_object(filter_path, self))

        self.inventory = InventoryDbPlugin()

    def schedule(self, plugin, context, lb):
        # Load all BIG-IP devices
        lb_name = lb.name
        LOG.debug("lb_name here is %s ", lb_name)

        # if found, store the device, to schedule to it
        the_inactive_dev = []
        if (
            lb_name
            and cfg.CONF.special_lb_name_prefix
            # it is now required SPECIAL_XXXXXXXX included in lb_name;
            # which means abc_SPECIAL_XXXXXXXX or SPECIAL_XXXXXXXX_def
            # or ghi_SPECIAL_XXXXXXXX_jk can all satisfy. Earlier rule
            # was lb_name starts with special_lb_name_prefix and ends
            # with XXXXXXXX (the first 8 char of inactive device uuid)
            and cfg.CONF.special_lb_name_prefix in lb_name
        ):
            inactive_devices = self.load_inactive_device(context)
            LOG.debug("inactive_devices here is %s ", inactive_devices)
            for each in inactive_devices:
                id_prefix = each["id"][:8]
                match_regex = cfg.CONF.special_lb_name_prefix + id_prefix
                if match_regex in lb_name:
                    LOG.debug("match_regex here is %s ", match_regex)
                    LOG.debug("chooses inactive device here %s ", each["id"])
                    LOG.debug(each)
                    the_inactive_dev.append(each)
                    break

        if the_inactive_dev:
            candidates = the_inactive_dev
        else:
            udms = self.load_user_device_maps(context, lb.tenant_id)
            if len(udms) > 0:
                candidates = self.load_dedicated_devices(context, udms)
            else:
                candidates = self.load_shared_devices(context)

        LOG.debug("the candidates are: %s", candidates)
        if len(candidates) <= 0:
            raise NoActiveLbaasDevice(loadbalancer_id=lb.id)

        device_ids = [device["id"] for device in candidates]
        bindings = self.load_bindings(context, device_ids=device_ids)
        lbs = self.load_loadbalancers(context, plugin, bindings, device_ids)

        # Construct a map for filters in order to get the loadbalancers
        # of every device candidates a little bit easier
        lb_map = {}
        for device_id in device_ids:
            lb_map[device_id] = []
            lb_ids = []
            for binding in bindings:
                if binding.device_id == device_id:
                    lb_ids.append(binding.loadbalancer_id)
            for a_lb in lbs:
                if a_lb["id"] in lb_ids:
                    lb_map[device_id].append(a_lb)

        # Select the desired device
        for filter in self.filters:
            LOG.debug("Before filter %s device candidates are %s",
                      type(filter).__name__, [i["id"] for i in candidates])
            candidates = filter.select(context, plugin, lb, candidates,
                                       bindings=bindings, existing_lbs=lbs,
                                       lb_map=lb_map)
            LOG.debug("After filter %s device candidates are %s",
                      type(filter).__name__, [i["id"] for i in candidates])
            if len(candidates) <= 0:
                break

        if len(candidates) <= 0:
            raise NoEligibleLbaasDevice(loadbalancer_id=lb.id)
        else:
            return candidates[0]

    def load_devices(self, context, filters=None):
        # Switch to admin context, so that driver code can query
        # devices onboared by admin when processing user request
        if context.is_admin:
            admin_ctx = context
        else:
            admin_ctx = ncontext.get_admin_context()
        devices = []
        devices_db = self.inventory.get_devices(admin_ctx, filters)
        device_ids = [device["id"] for device in devices_db]
        members = self.inventory.get_members(
            context, {"device_id": device_ids})
        for device_db in devices_db:
            device = device_db.copy()
            device["device_info"]["members"] = []
            for member in members:
                if member["device_id"] == device["id"]:
                    device["device_info"]["members"].append(member.copy())
            devices.append(device)
        return devices

    def load_shared_devices(self, context):
        filters = {"shared": [True], "admin_state_up": [True]}
        return self.load_devices(context, filters)

    def load_user_device_maps(self, context, tenant_id):
        if not hasattr(self.driver.plugin.db,
                       'get_user_device_maps_as_api_dict'):
            LOG.debug("No user-device-map db interface. "
                      "Skip to load dedicated devices.")
            return []

        maps = self.driver.plugin.db.get_user_device_maps_as_api_dict(
            context, {"user_id": [tenant_id]})
        LOG.debug("The user-device-map for user_id %s is %s", tenant_id, maps)
        return maps

    def load_dedicated_devices(self, context, maps):
        ipv4_filter = {"mgmt_ipv4": []}
        ipv6_filter = {"mgmt_ipv6": []}
        for map in maps:
            node_ip = map["node_ip"]
            for ips_str in node_ip.split(";"):
                ips = ips_str.split(",")
                for ip in ips:
                    if "." in ip:
                        ipv4_filter["mgmt_ipv4"].append(ip)
                    elif ":" in ip:
                        ipv6_filter["mgmt_ipv6"].append(str(
                            ipaddress.IPv6Address(
                                unicode(ip)).compressed))

        members = []
        if len(ipv4_filter["mgmt_ipv4"]) > 0:
            members_db = self.inventory.get_members(context, ipv4_filter)
            for member_db in members_db:
                members.append(member_db.copy())
        if len(ipv6_filter["mgmt_ipv6"]) > 0:
            members_db = self.inventory.get_members(context, ipv6_filter)
            for member_db in members_db:
                members.append(member_db.copy())

        if len(members) == 0:
            raise NoDedicatedLbaasDevice()

        device_ids = []
        for member in members:
            if member["device_id"] not in device_ids:
                device_ids.append(member["device_id"])

        device_filter = {
            "id": device_ids,
            "shared": [False],
            "admin_state_up": [True]
        }

        devices = self.load_devices(context, device_filter)

        # TODO(qzhao): Need to ensure consistency between user-device-map
        # and inventory. For example, all device member mgmt ips must be
        # in the same part of node_ip string.

        return devices

    def load_inactive_device(self, context):
        return self.load_devices(context, {"admin_state_up": [False]})

    def load_device(self, context, id):
        devices = self.load_devices(context, {"id": [id]})
        if len(devices) > 0:
            return devices[0]
        else:
            return None

    def load_bindings(self, context, device_ids=[]):
        if not device_ids:
            query = context.session.query(
                agent_scheduler.LoadbalancerAgentBinding
            ).populate_existing().all()
        else:
            query = context.session.query(
                agent_scheduler.LoadbalancerAgentBinding
            ).populate_existing().filter(
                agent_scheduler.LoadbalancerAgentBinding.device_id.in_(
                    device_ids
                )
            )
        bindings = [binding for binding in query]
        return bindings

    def load_loadbalancers(self, context, plugin, bindings, device_ids):
        # Load all existing loadbalancers on candidate devices
        lb_ids = []
        for binding in bindings:
            if binding.device_id in device_ids:
                lb_ids.append(binding.loadbalancer_id)

        filters = {"id": lb_ids}
        lbs = plugin.db.get_loadbalancers(context, filters=filters)

        # SDN vendor might modify db interface to return dict instead of
        # loadbalancer object. Convert them to dict in order to handle them
        # in a unified way.
        lb_dicts = []
        for lb in lbs:
            if type(lb) != dict:
                lb_dicts.append(lb.to_api_dict(full_graph=False))
            else:
                lb_dicts.append(lb)

        return lb_dicts


class DeviceFilter(object):

    def __init__(self, scheduler):
        """Initialze Device Filter"""
        self.scheduler = scheduler

    def load_config(self):

        # default config
        self.constant = {}
        self.constant["flavor"] = constants_v2.FLAVOR_CONN_MAP
        self.constant["capacity"] = constants_v2.CAPACITY_MAP

        # customized config
        if config.cust_cfg is None:
            msg = "customerized configuration is None, check " \
                "your /etc/neutron/services/f5/scheduler.json file."
            raise Exception(msg)
        self.cust_cfg = config.cust_cfg

    def select(self, context, plugin, lb, candidates, **kwargs):
        raise NotImplementedError()


class RandomFilter(DeviceFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        if len(candidates) > 0:
            return [random.choice(candidates)]
        else:
            return candidates


class AvailabilityZoneFilter(f5_agent_scheduler.AvailabilityZoneFilter):
    pass


class OfflineDeviceFilter(DeviceFilter):
    def select(self, context, plugin, lb, candidates, **kwargs):
        result = []
        for candidate in candidates:
            select_it = True
            for member in candidate["device_info"]["members"]:
                ops = member["operating_status"]
                status = ops.get("status", "OFFLINE")
                if status != "ONLINE":
                    select_it = False

            if select_it:
                result.append(candidate)

        return result


class OfflineDeviceMemberFilter(DeviceFilter):
    def select(self, context, plugin, lb, candidates, **kwargs):
        result = []
        for candidate in candidates:
            online_members = []
            for member in candidate["device_info"]["members"]:
                ops = member["operating_status"]
                status = ops.get("status", "OFFLINE")
                if status == "ONLINE":
                    online_members.append(member)
            candidate["device_info"]["members"] = online_members

            if len(online_members) > 0:
                result.append(candidate)

        return result


class FlavorFilter(DeviceFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        flavor = lb.flavor
        if flavor < 1 or 8 < flavor < 11 or flavor > 13:
            # Invalid flavor values
            return []

        result = []
        for candidate in candidates:
            lic_types = []
            for bigip in candidate["device_info"]["members"]:
                lic = bigip["device_info"]["license"].values()[0]
                if lic == "VE, LAB":
                    lic_types.append("LAB")
                elif lic.startswith("VE"):
                    lic_types.append("VE")
                else:
                    lic_types.append("HW")

            select_it = True
            if 1 <= flavor <= 8:
                # Select BIG-IP HW or BIG-IP VE with dev license
                for lic_type in lic_types:
                    if lic_type == "VE":
                        select_it = False
            elif 11 <= flavor <= 13:
                # Select BIG-IP VE
                for lic_type in lic_types:
                    if lic_type == "HW":
                        select_it = False

            if select_it:
                result.append(candidate)

        return result


class CapacityFilter(DeviceFilter):

    def __init__(self, scheduler):
        super(CapacityFilter, self).__init__(scheduler)
        self.load_config()

    def load_config(self):
        super(CapacityFilter, self).load_config()

        if self.cust_cfg.get("flavor"):
            LOG.debug("merge config: customized flavors")
            config.merge_cfg_dict(
                self.constant["flavor"],
                self.cust_cfg["flavor"]
            )

        if self.cust_cfg.get("capacity") and \
                self.cust_cfg.get("capacity").get("license"):
            LOG.debug(
                "merge config: customized capacity licenses"
            )
            config.merge_cfg_dict(
                self.constant["capacity"]["license"],
                self.cust_cfg["capacity"]["license"]
            )

        capacity_const = self.constant["capacity"]
        if "license" in capacity_const:
            for lic in capacity_const["license"]:
                lic_const = capacity_const["license"][lic]
                # Negative value means unlimited
                for key in ["bandwidth", "lod", "rod", "cod"]:
                    if key in lic_const and lic_const[key] < 0:
                        lic_const[key] = sys.maxint

                # Fix invalid values
                for key in ["por", "poc"]:
                    if key in lic_const and \
                       (lic_const[key] < 0 or lic_const[key] > 1):
                        lic_const[key] = 1.00

    def select(self, context, plugin, lb, candidates, **kwargs):
        result = []
        for candidate in candidates:
            capacity = self.calculate(context, plugin, lb,
                                      candidate, **kwargs)
            LOG.debug("Capacity of candidate %s is %s",
                      candidate["id"], capacity)
            if capacity >= 1:
                candidate["capacity"] = capacity
                result.append(candidate)
        return sorted(result, key=lambda x: x["capacity"], reverse=True)

    def calculate(self, context, plugin, lb, candidate, **kwargs):
        lb_map = kwargs.get("lb_map", {})

        rolb = 0
        colb = 0
        flavor = str(lb.flavor)
        flavor_const = self.constant["flavor"]
        if flavor in flavor_const:
            rolb = flavor_const[flavor]["rate_limit"]
            colb = flavor_const[flavor]["connection_limit"]

        device_id = candidate["id"]
        lbs = lb_map[device_id]

        LB = len(lbs)
        ROLB = 0
        COLB = 0
        for a_lb in lbs:
            its_flavor = str(a_lb["flavor"])
            if its_flavor in flavor_const:
                ROLB += flavor_const[its_flavor]["rate_limit"]
                COLB += flavor_const[its_flavor]["connection_limit"]

        result = []
        # If the device contains multiple bigips, select the
        # minimum capacity of every bigips.
        for bigip in candidate["device_info"]["members"]:
            capacity = self.calculate_bigip(
                bigip, rolb=rolb, colb=colb,
                LB=LB, ROLB=ROLB, COLB=COLB
            )
            LOG.debug("BIG-IP %s capacity is %s", bigip["mgmt_ipv4"], capacity)
            result.append(capacity)

        if len(result) > 0:
            return sorted(result)[0]
        else:
            return 0

    def calculate_bigip(self, bigip, **kwargs):
        rolb = kwargs.get("rolb", 0)
        colb = kwargs.get("colb", 0)
        LB = kwargs.get("LB", 0)
        ROLB = kwargs.get("ROLB", 0)
        COLB = kwargs.get("COLB", 0)

        capacity_const = self.constant["capacity"]
        license = bigip["device_info"]["license"].values()[0]

        if "license" not in capacity_const:
            msg = "'license' is not in scheduler.json, " \
                "skip capacity calculating.\n"
            LOG.warning(msg)
            return 0
        capacity = capacity_const["license"]

        if license in capacity:
            constant = capacity[license]
        elif "default" in capacity:
            msg = "license: %s use default" \
                "values in scheduler.json.\n" % license
            LOG.debug(msg)
            constant = capacity["default"]
        else:
            msg = "%s license corresponding capacity value not " \
                "found in %s, and not default value config" % (
                    license, capacity_const)
            LOG.warning(msg)
            return 0

        lod = constant["lod"]
        rod = constant["rod"]
        cod = constant["cod"]
        por = constant["por"]
        poc = constant["poc"]

        X = lod - LB
        Y = ((rod * por) - ROLB) / rolb
        Z = ((cod * poc) - COLB) / colb

        return min(X, Y, Z)


class BandwidthCapacityFilter(CapacityFilter):

    def __init__(self, scheduler):
        super(BandwidthCapacityFilter, self).__init__(scheduler)

    def select(self, context, plugin, lb, candidates, **kwargs):
        result = []

        # Only VE flavor 11/12/13 requires to calculate bandwidth
        flavor = lb.flavor
        if flavor < 11 or flavor > 13:
            return candidates

        for candidate in candidates:
            capacity = self.calculate(context, plugin, lb,
                                      candidate, **kwargs)
            LOG.debug("Capacity of candidate %s is %s",
                      candidate["id"], capacity)
            if capacity >= 0:
                candidate["bandwidth_capacity"] = capacity
                result.append(candidate)
        return sorted(result, key=lambda x: x["bandwidth_capacity"],
                      reverse=True)

    def calculate(self, context, plugin, lb, candidate, **kwargs):
        lb_map = kwargs.get("lb_map", {})
        device_id = candidate["id"]
        lbs = lb_map[device_id]

        osr, BC_device = self.device_osr_capacity(candidate)

        N_xy = {}
        Q_xy = {}
        R_xy = {}
        RR_xy = {}

        N_xy[lb.vip_subnet_id] = {"11": 0, "12": 0, "13": 0}
        Q_xy[lb.vip_subnet_id] = {"11": 0, "12": 0, "13": 0}
        R_xy[lb.vip_subnet_id] = {"11": 0, "12": 0, "13": 0}
        RR_xy[lb.vip_subnet_id] = {"11": 0, "12": 0, "13": 0}

        N_xy[lb.vip_subnet_id][str(lb.flavor)] = 1
        R_xy[lb.vip_subnet_id][str(lb.flavor)] = 1

        for a_lb in lbs:
            subnet = a_lb["vip_subnet_id"]
            flavor = str(a_lb["flavor"])

            if subnet not in N_xy:
                N_xy[subnet] = {"11": 0, "12": 0, "13": 0}
                Q_xy[subnet] = {"11": 0, "12": 0, "13": 0}
                R_xy[subnet] = {"11": 0, "12": 0, "13": 0}
                RR_xy[subnet] = {"11": 0, "12": 0, "13": 0}

            N_xy[subnet][flavor] += 1
            Q_xy[subnet][flavor] = N_xy[subnet][flavor] / osr
            R_xy[subnet][flavor] = N_xy[subnet][flavor] % osr

        for x in R_xy.keys():
            # Fill the largest flavor cart
            RR_xy[x]["13"] = R_xy[x]["13"]
            # The last non-empty cart is nec
            nec = -1
            if R_xy[x]["13"] > 0:
                nec = 0

            f = ["13", "12", "11"]
            # Start from the second largest flavor
            y = 1
            while y < len(f):
                if R_xy[x][f[y]] > 0 and nec >= 0:
                    # Get on the last non-empty cart
                    RR_xy[x][f[nec]] += R_xy[x][f[y]]
                    rest = RR_xy[x][f[nec]] - osr

                    # if the last non-empty cart is full, let the rest ones
                    # to get off and get on the cart of flavor y
                    if rest > 0:
                        RR_xy[x][f[nec]] = osr
                        RR_xy[x][f[y]] = rest
                        nec = y
                elif R_xy[x][f[y]] > 0 and nec < 0:
                    # If no larger cart, get on the cart of flavor y
                    RR_xy[x][f[y]] = R_xy[x][f[y]]
                    nec = y

                # Goto next smaller flavor
                y += 1

        BC = {}
        BC_all = 0
        for x in N_xy.keys():
            BC[x] = 500 * (Q_xy[x]["13"] + int(RR_xy[x]["13"] > 0)) + \
                    200 * (Q_xy[x]["12"] + int(RR_xy[x]["12"] > 0)) + \
                    100 * (Q_xy[x]["11"] + int(RR_xy[x]["11"] > 0))
            BC_all += BC[x]

        LOG.debug("Bandwidth capacity of every subnet is %s", BC)

        return BC_device - BC_all

    def device_osr_capacity(self, device):
        osr = []
        bc = []
        user_osr = device.get("osr", 0)
        capacity_const = self.constant["capacity"]
        for bigip in device["device_info"]["members"]:
            lic = bigip["device_info"]["license"].values()[0]
            if lic in capacity_const["license"]:
                osr.append(capacity_const["license"][lic]["osr"])
                bc.append(capacity_const["license"][lic]["bandwidth"])
            else:
                osr.append(capacity_const["license"]["default"]["osr"])
                bc.append(capacity_const["license"]["default"]["bandwidth"])
        return user_osr or min(osr), min(bc)


class SubnetAffinityFilter(DeviceFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        lb_map = kwargs.get("lb_map", {})
        subnet_id = lb.vip_subnet_id
        result = []

        for candidate in candidates:
            device_id = candidate["id"]
            lbs = lb_map[device_id]
            for a_lb in lbs:
                if subnet_id == a_lb["vip_subnet_id"]:
                    result.append(candidate)
                    break

        if len(result) > 0:
            return result
        else:
            return candidates
