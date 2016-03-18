
import datetime
import json
import netaddr
import sys
from time import time
import uuid
from pprint import pprint

from oslo_config import cfg
import oslo_messaging as messaging

from neutron.api.v2 import attributes
from neutron.common import constants as q_const
from neutron.common import rpc as q_rpc
from neutron import context
from neutron.db import agents_db
from neutron.plugins.common import constants

from f5_openstack_agent.lbaasv2.drivers.bigip import constants_v2

from neutron_lbaas.services.loadbalancer.drivers.abstract_driver \
    import LoadBalancerAbstractDriver  # @UnresolvedImport @Reimport
from neutron_lbaas.extensions \
    import lbaas_agentscheduler  # @UnresolvedImport @Reimport
from neutron_lbaas.db.loadbalancer import loadbalancer_db as lb_db
from oslo_log import log as logging
from oslo_utils import importutils
from neutron_lbaas.extensions.loadbalancer \
    import MemberNotFound  # @UnresolvedImport @Reimport
from neutron_lbaas.extensions.loadbalancer \
    import PoolNotFound  # @UnresolvedImport @Reimport
from neutron_lbaas.extensions.loadbalancer \
    import VipNotFound  # @UnresolvedImport @Reimport
from neutron_lbaas.extensions.loadbalancer \
    import HealthMonitorNotFound  # @UnresolvedImport @Reimport

import f5_openstack_agent.lbaasv2.drivers.bigip.constants_v2 

if __name__ == '__main__':

    with open('service.json') as service_data:
        data = json.load(service_data)

    service = data['service']
    loadbalancer_id = service['loadbalancer']['id']
    environment_prefix = 'Test'
    topic = '%s_%s' % (constants_v2.TOPIC_PROCESS_ON_HOST_V2, environment_prefix)
    default_version = '1.0'

    q_rpc.init(cfg.CONF)

    transport = messaging.get_transport(cfg.CONF)
    target = messaging.Target(topic=topic)
    client = messaging.RPCClient(transport, target)

    ctxt=context.get_admin_context().to_dict()

    print "Create Network"
    net = client.call(ctxt, 'create_network',
                      tenant_id='c4021c6afe1c4c01892bf9f12eacace7',
                      name='net1',
                      admin_state_up=True,
                      shared=False
    )
    print net
    
    print "Create Subnet"
    cidr='192.168.101.0/24'
    subnet_name='subnet1'
    subnet = client.call(ctxt, 'create_subnet',
                         tenant_id='c4021c6afe1c4c01892bf9f12eacace7',
                         network_id=net['id'],
                         ip_version=4,
                         name=subnet_name,
                         cidr=cidr,
                         shared=False,
                         enable_dhcp=False
    )
    print subnet

    print "Create Port on Subnet"
    port = client.call(ctxt, 'create_port_on_subnet_with_specific_ip',
                       subnet_id=subnet['id'],
                       mac_address="aa:bb:cc:dd:ee:ff",
                       name="test_port",
                       ip_address='192.168.101.10'
    )
    print port
    ret = client.call(ctxt, 'delete_port', port_id=port['id'])

    print "Allocate Specific Address on Subnet"
    port = client.call(ctxt, 'allocate_fixed_address_on_subnet',
                       subnet_id=subnet['id'])
    print port
    ret = client.call(ctxt, 'delete_port', port_id=port['id'])

    print "Allocate Specific Fixed Address on Subnet"
    port = client.call(ctxt, 
                       'allocate_specific_fixed_address_on_subnet',
                       subnet_id=subnet['id'],
                       ip_address='192.168.101.101'
    )
    print port

    print "Deallocate Specific Fixed Address on Subnet"
    client.call(ctxt,
                'deallocate_fixed_address_on_subnet',
                subnet_id=subnet['id'],
                fixed_addresses=['192.168.101.101'])
    print port

    ret = client.call(ctxt, 'delete_port', port_id=port['id'])
    ret = client.call(ctxt, 'delete_subnet', subnet_id=subnet['id'])
    ret = client.call(ctxt, 'delete_network', network_id=net['id'])

