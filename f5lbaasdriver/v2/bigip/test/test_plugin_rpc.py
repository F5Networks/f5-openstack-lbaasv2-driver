import mock
import pytest

import neutron.api.v2.attributes
from neutron_lib import constants as neutron_const

import f5lbaasdriver.v2.bigip.plugin_rpc 


@pytest.fixture
@mock.patch("f5lbaasdriver.v2.bigip.plugin_rpc.LBaaSv2PluginCallbacksRPC."
            "__init__")
def fully_mocked_target(init):
    init.return_value = None
    target = f5lbaasdriver.v2.bigip.plugin_rpc.LBaaSv2PluginCallbacksRPC()
    return target


@pytest.fixture
def neutron_attributes(request):
    hold_attributes = neutron.api.v2.attributes
    def finalizer():
        neutron.api.v2.attributes = hold_attributes
    request.addfinalizer(finalizer)
    neutron.api.v2.attributes = mock.Mock()
    return neutron.api.v2.attributes

@pytest.fixture
def neutron_extensions(request):
    hold_extensions = neutron.extensions
    def finalizer():
        neutron.extensions = hold_extensions
    request.addfinalizer(finalizer)
    neutron.extensions = mock.Mock()
    return neutron.extensions

def test_create_port_on_subnet(fully_mocked_target, neutron_attributes,
                               neutron_extensions):
    portbindings = neutron_extensions.portbindings
    target = fully_mocked_target
    context = mock.Mock()
    # fake data manipulations....
    # args...
    fake_args = ['subnet_id', 'mac_address', 'name', 'host', 'device_id',
                 'vnic_type', 'binding_profile']
    portbindings_attrs = ['VNIC_NORMAL', 'HOST_ID', 'VNIC_TYPE', 'PROFILE']
    fake_args = {x: x for x in fake_args}
    fake_args['binding_profile'] = {}
    # port bindings...
    for attr in portbindings_attrs:
        setattr(portbindings, attr, attr)
    fake_args['vnic_type'] = portbindings.VNIC_NORMAL
    # fake validation data...
    subnet = {'id': 'subnet_id', 'tenant_id': 'tenant_id', 
              'network_id': 'network_id'}
    port = {'id': 'id'}
    device_ips = [{'subnet_id': subnet['id']}]
    port_data = {
        'tenant_id': subnet['tenant_id'],
        'name': fake_args['name'],
        'network_id': subnet['network_id'],
        'mac_address': fake_args['mac_address'],
        'admin_state_up': True,
        'device_owner': 'network:f5lbaasv2',
        'status': neutron_const.PORT_STATUS_ACTIVE,
        'fixed_ips': device_ips,
        'device_id': fake_args['device_id'],
        'binding:host_id': fake_args['host'],
        'binding:vnic_type': portbindings.VNIC_NORMAL,
        'binding:profile': {}}
    update_data = {'status': neutron_const.PORT_STATUS_ACTIVE}
    expected_create_port_args = (context, {'port': port_data})
    expected_update_port_args = \
        (context, port['id'], {'port': update_data})
    # attach our mock interactions...
    target.driver = mock.Mock()
    target.driver.plugin.db._core_plugin.get_subnet.return_value = subnet
    target.driver.plugin.db._core_plugin.create_port.return_value = port
    # test...
    assert port == target.create_port_on_subnet(context, **fake_args)
    # validate...
    assert target.driver.plugin.db._core_plugin.get_subnet.call_count
    assert target.driver.plugin.db._core_plugin.create_port.call_count
    assert target.driver.plugin.db._core_plugin.create_port.\
        call_args_list[0][0] == expected_create_port_args
    assert target.driver.plugin.db._core_plugin.update_port.\
        call_args_list[0][0] == expected_update_port_args
