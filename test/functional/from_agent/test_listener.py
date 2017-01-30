# -*- coding: utf-8 -*-
'''
test_requirements = {'devices':         [VE],
                     'openstack_infra': []}

'''
# Copyright 2015-2106 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json

from f5_openstack_agent.lbaasv2.drivers.bigip.listener_service import \
    ListenerServiceBuilder
from f5_openstack_agent.lbaasv2.drivers.bigip.loadbalancer_service import \
    LoadBalancerServiceBuilder


def test_create_listener(bigip):
    bigips = [bigip]
    lb_service = LoadBalancerServiceBuilder()
    listener_builder = ListenerServiceBuilder()
    service = json.load(open("../../service.json"))["service"]

    try:
        # create partition
        lb_service.prep_service(service, bigips)

        # create BIG-IP® virtual servers
        listeners = service["listeners"]
        loadbalancer = service["loadbalancer"]

        for listener in listeners:
            # create a service object in form expected by builder
            svc = {"loadbalancer": loadbalancer,
                   "listener": listener}

            # create
            listener_builder.create_listener(svc, bigips)

            # validate
            l = listener_builder.get_listener(svc, bigips[0])
            assert l.name == listener["name"]
            print "Created listener: " + l.name

            # delete
            listener_builder.delete_listener(svc, bigips)

    finally:
        lb_service.delete_partition(service, bigips)
