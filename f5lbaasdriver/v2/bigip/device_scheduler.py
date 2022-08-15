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

import json
import random

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from neutron_lbaas.extensions import lbaas_agentschedulerv2

LOG = logging.getLogger(__name__)


class NoEligibleLbaasDevice(lbaas_agentschedulerv2.NoEligibleLbaasAgent):
    message = ("No eligible BIG-IP found "
               "for loadbalancer %(loadbalancer_id)s.")


class NoActiveLbaasDevice(lbaas_agentschedulerv2.NoActiveLbaasAgent):
    message = ("No active BIG-IP found "
               "for loadbalancer %(loadbalancer_id)s.")


class BadDeviceInventory(lbaas_agentschedulerv2.NoActiveLbaasAgent):
    message = ("Fail to load device inventory: %(loadbalancer_id)s")


class DeviceSchedulerNG(object):
    """NextGen Device Scheduler for LBaaSv2"""

    def __init__(self):
        super(DeviceSchedulerNG, self).__init__()
        self.filters = []
        names = cfg.CONF.device_filters
        for name in names:
            filter_path = ".".join([DeviceSchedulerNG.__module__, name])
            self.filters.append(importutils.import_object(filter_path, self))

        self.inventory = None

    def schedule(self, plugin, context, lb):
        # Load all BIG-IP devices
        candidates = self.load_active_devices()
        if len(candidates) <= 0:
            raise NoActiveLbaasDevice(loadbalancer_id=lb.id)

        # Select the desired device
        for filter in self.filters:
            LOG.debug("Before filter %s device candidates are %s",
                      type(filter).__name__, [i["id"] for i in candidates])
            candidates = filter.select(context, plugin, lb, candidates)
            LOG.debug("After filter %s device candidates are %s",
                      type(filter).__name__, [i["id"] for i in candidates])
            if len(candidates) <= 0:
                break

        if len(candidates) <= 0:
            raise NoEligibleLbaasDevice(loadbalancer_id=lb.id)
        else:
            return candidates[0]

    def load_inventory(self):
        try:
            f = open(cfg.CONF.device_inventory)
            self.inventory = json.load(f)
            f.close()
        except Exception as ex:
            raise BadDeviceInventory(loadbalancer_id=ex.message)

        for device_id in self.inventory.keys():
            if "id" not in self.inventory[device_id]:
                self.inventory[device_id]["id"] = device_id

    def load_active_devices(self):
        if not self.inventory:
            self.load_inventory()

        devices = []
        for device_id in self.inventory.keys():
            device = self.inventory[device_id]
            if device["admin_state_up"]:
                devices.append(device)
        return devices

    def load_device(self, id):
        if not self.inventory:
            self.load_inventory()

        return self.inventory.get(id, {})


class DeviceFilter(object):

    def __init__(self, scheduler):
        """Initialze Device Filter"""
        self.scheduler = scheduler

    def select(self, context, plugin, lb, candidates, **kwargs):
        raise NotImplementedError()


class RandomFilter(DeviceFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        if len(candidates) > 0:
            return [random.choice(candidates)]
        else:
            return candidates


class AvailabilityZoneFilter(DeviceFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        return candidates
