import os
import sys
import time

from neutron.common import rpc as q_rpc
from neutron import context
from neutronclient.v2_0 import client as q_client

from oslo_config import cfg
import oslo_messaging as messaging

from f5lbaasdriver.v2.bigip import constants_v2

lb_dict = {
    'loadbalancer': {
        'vip_subnet_id': '85540bed-ea58-478f-b408-b51ff5c9e95e',
        'tenant_id': 'b8b1cb597c8b4cc9b452625c1c6d7da2',
        'name': 'lb1'
    }
}


def main():
    username = ""
    password = ""
    auth_url = ""

    if 'OS_USERNAME' in os.environ:
        username = os.environ['OS_USERNAME']
    else:
        print("OS_USERNAME not defined in environment")
        sys.exit(1)

    if 'OS_PASSWORD' in os.environ:
        password = os.environ['OS_PASSWORD']
    else:
        print("OS_PASSWORD not defined in environment")
        sys.exit(1)

    if 'OS_TENANT_NAME' in os.environ:
        tenant_name = os.environ['OS_TENANT_NAME']
    else:
        print("OS_TENANT_NAME not defined in environment")
        sys.exit(1)

    if 'OS_AUTH_URL' in os.environ:
        auth_url = os.environ['OS_AUTH_URL']
    else:
        print("OS_AUTH_URL not defined in environment")
        sys.exit(1)

    neutron = q_client.Client(username=username,
                              password=password,
                              tenant_name=tenant_name,
                              auth_url=auth_url)

    subnets = neutron.list_subnets()['subnets']
    for subnet in subnets:
        if subnet['name'] == 'private-subnet':
            lb_dict['loadbalancer']['vip_subnet_id'] = subnet['id']
            lb_dict['loadbalancer']['tenant_id'] = subnet['tenant_id']

    neutron.create_loadbalancer(lb_dict)
    loadbalancers = neutron.list_loadbalancers()['loadbalancers']
    for loadbalancer in loadbalancers:
        if loadbalancer['name'] == lb_dict['loadbalancer']['name']:
            break

    environment_prefix = 'Test'
    topic = '%s_%s'\
        % (constants_v2.TOPIC_PROCESS_ON_HOST_V2, environment_prefix)
    print(topic)

    q_rpc.init(cfg.CONF)

    transport = messaging.get_transport(cfg.CONF)
    target = messaging.Target(topic=topic)
    rpc_client = messaging.RPCClient(transport, target)

    ctxt = context.get_admin_context().to_dict()
    print(loadbalancer['id'])
    time.sleep(5)
    service = rpc_client.call(ctxt, 'get_service_by_loadbalancer_id',
                              loadbalancer_id=loadbalancer['id'],
                              global_routed_mode=True,
                              host=None)
    print(service)

    neutron.delete_loadbalancer(loadbalancer['id'])

if __name__ == '__main__':
    main()
