# Copyright 2016 F5 Networks Inc.
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

from neutron.plugins.ml2 import db
from neutron.plugins.ml2 import models
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class DisconnectedService(object):
    def __init__(self):
        pass

    # Retain this method for future use in case a particular ML2 implementation
    # decouples network_id from physical_network name.  The implementation in
    # neutron db.py requires a network_id.
    def get_network_segments(self, session):
        with session.begin(subtransactions=True):
            query = (session.query(models.NetworkSegment).
                     order_by(models.NetworkSegment.segment_index))
            records = query.all()
            result = {}
            for record in records:
                if record.network_id not in result:
                    result[record.network_id] = []
                result[record.network_id].append(db._make_segment_dict(record))
            return result

    def get_network_segment(self, context, agent_configuration, network):
        data = None
        network_segment_physical_network = \
            agent_configuration.get('network_segment_physical_network', None)
        if network_segment_physical_network:
            # look up segment details in the ml2_network_segments table
            segments = db.get_network_segments(context.session, network['id'])
            for segment in segments:
                if (network_segment_physical_network ==
                        segment['physical_network']):
                    data = segment
                    break
            if not data:
                LOG.error('network_id %s does not match physical_network %s' %
                          (network['id'], network_segment_physical_network))
        else:
            # neutron is expected to provide this data immediately
            data = {
                'segmentation_id': network['provider:segmentation_id']
            }
            if 'provider:network_type' in network:
                data['network_type'] = network['provider:network_type']
        return data
