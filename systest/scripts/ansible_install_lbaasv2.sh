#!/usr/bin/env bash

set -ex

OS_CONTROLLER_IP=`/tools/bin/tlc --sid ${TEST_SESSION} symbols \
    | grep openstack_controller1ip_data_direct \
    | awk '{print $3}' | xargs`
SSH_CMD="ssh -i /home/jenkins/.ssh/id_rsa -o StrictHostKeyChecking=no testlab@${OS_CONTROLLER_IP}"
BIGIP_IP=`${SSH_CMD} "cat /home/testlab/ve_mgmt_ip"`
BIGIP_IP=${BIGIP_IP%%[[:cntrl:]]}
AGENT_LOC=git+https://github.com/F5Networks/f5-openstack-agent.git@${BRANCH}
DRIVER_LOC=${DRIVER_PIP_INSTALL_LOCATION}
NEUTRON_DRIVER_LOC=https://raw.githubusercontent.com/F5Networks/neutron-lbaas/stable/${TEST_OPENSTACK_DISTRO}/neutron_lbaas/drivers/f5/driver_v2.py

# Since we don't do anything special in the __init__.py file, we can pull it from anywhere for now
NEUTRON_INIT_LOC=https://raw.githubusercontent.com/F5Networks/neutron-lbaas/v9.1.0/neutron_lbaas/drivers/f5/__init__.py


EXTRA_VARS="agent_pkg_location=${AGENT_LOC} driver_pkg_location=${DRIVER_LOC} neutron_lbaas_driver_location=${NEUTRON_DRIVER_LOC}"

if [[ $TEST_OPENSTACK_CLOUD == 'undercloud' ]]; then
    GLOBAL_ROUTED_MODE="False"
    if [[ $TEST_TENANT_NETWORK_TYPE == 'vlan' ]]; then
        ADVERTISED_TUNNEL_TYPES=""
    else
        ADVERTISED_TUNNEL_TYPES=${TEST_TENANT_NETWORK_TYPE}
    fi
    EXTRA_VARS="${EXTRA_VARS} advertised_tunnel_types=${ADVERTISED_TUNNEL_TYPES}"
else
    GLOBAL_ROUTED_MODE="True"
fi

EXTRA_VARS="${EXTRA_VARS} neutron_lbaas_init_location=${NEUTRON_INIT_LOC} restart_all_neutron_services=true remote_user=testlab"
EXTRA_VARS="${EXTRA_VARS} f5_global_routed_mode=${GLOBAL_ROUTED_MODE} bigip_netloc=${BIGIP_IP} agent_service_name=f5-openstack-agent.service"
EXTRA_VARS="${EXTRA_VARS} use_barbican_cert_manager=True neutron_lbaas_shim_install_dest=/usr/lib/python2.7/site-packages/neutron_lbaas/drivers/f5"
sudo -E chown -Rf jenkins:jenkins /home/jenkins/container_mailbox
bash -c "echo [hosts] > /home/jenkins/container_mailbox/ansible_conf.ini"
bash -c "echo \"${OS_CONTROLLER_IP} ansible_ssh_common_args='-o StrictHostKeyChecking=no' host_key_checking=False ansible_connection=ssh ansible_ssh_user=testlab ansible_ssh_private_key_file=/root/id_rsa\" >> /home/jenkins/container_mailbox/ansible_conf.ini"

sudo -E docker pull docker-registry.pdbld.f5net.com/f5-openstack/ansiblemicroservice-prod/newton:latest
sudo -E docker run \
--volumes-from `hostname | xargs` \
docker-registry.pdbld.f5net.com/f5-openstack/ansiblemicroservice-prod/newton:latest \
--extra-vars "${EXTRA_VARS}"
