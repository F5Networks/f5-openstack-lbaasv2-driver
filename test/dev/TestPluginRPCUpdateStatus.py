
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
from neutron_lbaas.services.loadbalancer import constants as lb_const
from f5_openstack_agent.lbaasv2.drivers.bigip import constants_v2

from neutron_lbaas.services.loadbalancer.drivers.abstract_driver \
    import LoadBalancerAbstractDriver  # @UnresolvedImport @Reimport
from neutron_lbaas.extensions \
    import lbaas_agentscheduler  # @UnresolvedImport @Reimport
from neutron_lbaas.db.loadbalancer import loadbalancer_db as lb_db
from oslo_log import log as logging
from oslo_utils import importutils

import f5_openstack_agent.lbaasv2.drivers.bigip.constants_v2 

def make_msg(method, **kwargs):
    return {'method': method,
            'args': kwargs}

if __name__ == '__main__':

    args = sys.argv
    lb_id = args[1]

    environment_prefix = 'Test'
    topic = '%s_%s' % (constants_v2.TOPIC_PROCESS_ON_HOST_V2, environment_prefix)
    default_version = '1.0'

    q_rpc.init(cfg.CONF)

    transport = messaging.get_transport(cfg.CONF)
    target = messaging.Target(topic=topic)
    client = messaging.RPCClient(transport, target)

    ctxt=context.get_admin_context().to_dict()

    client.call(ctxt, 'update_loadbalancer_status',
                loadbalancer_id=lb_id,
                status=constants.ACTIVE,
                operating_status=lb_const.ONLINE
    )
