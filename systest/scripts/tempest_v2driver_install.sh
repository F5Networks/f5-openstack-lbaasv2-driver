#! /usr/bin/env bash
set -ex

BAHAMAS=$1
TESTSESSION=$2
BRANCH=$3
SUBJECTCODE_ID=$4
USER=$5

CONTROLLER_IPADDR=`ssh -oStrictHostKeyChecking=no -A builder@${BAHAMAS}\
              "/tools/bin/tlc --sid ${TESTSESSION} symbols "\
              "| grep -e'openstack_controller.*_data_direct' "\
              "| cut -d':' -f2 | tr -d '[:space:]'"`

SSH_TO_CONTROLLER="ssh -oStrictHostKeyChecking=no -A testlab@${CONTROLLER_IPADDR}"
SSH_WITH_KEYSTONE=${SSH_TO_CONTROLLER}" source keystonerc_testlab && " 

# SSH invocations
ICONTROL_IPADDR=`${SSH_TO_CONTROLLER} "cat ve_mgmt_ip"`
OS_AUTH_URL=`${SSH_WITH_KEYSTONE} "grep OS_AUTH_URL keystonerc_testlab"`
PUBLIC_ROUTER_ID=`${SSH_WITH_KEYSTONE} "neutron router-list -F id -F name "\
    "| grep tempest-mgmt-router | cut -d '|' -f 2  | xargs 2>/dev/null"`
PUBLIC_NETWORK_ID=`${SSH_WITH_KEYSTONE} "neutron net-list -F id -F name "\
    "| grep external_network | cut -d '|' -f 2  | xargs 2>/dev/null"`
OS_TENANT_ID=`${SSH_WITH_KEYSTONE} "keystone tenant-list "\
    "| grep testlab | cut -d '|' -f 2  | xargs 2>/dev/null"`
IMAGE_REF=`${SSH_WITH_KEYSTONE} "glance image-list"\
    "| grep cirros-0.3.4-x86_64-disk.qcow2 | cut -d '|' -f 2 | xargs 2>/dev/null"`

# post processing ('prepend export=') NOTE: OS_AUTH_URL needs no modification
CONTROLLER_IPADDR="export CONTROLLER_IPADDR="${CONTROLLER_IPADDR}
ICONTROL_IPADDR="export ICONTROL_IPADDR="${ICONTROL_IPADDR}
OS_AUTH_URL_V3=${OS_AUTH_URL%%5000/v2.0}"35357/v3"
OS_AUTH_URL_V3="export OS_AUTH_URL_V3"${OS_AUTH_URL_V3#export OS_AUTH_URL}
PUBLIC_ROUTER_ID="export PUBLIC_ROUTER_ID="${PUBLIC_ROUTER_ID}
PUBLIC_NETWORK_ID="export PUBLIC_NETWORK_ID="${PUBLIC_NETWORK_ID}
OS_TENANT_ID="export OS_TENANT_ID="${OS_TENANT_ID}
IMAGE_REF="export IMAGE_REF="${IMAGE_REF}

echo ${CONTROLLER_IPADDR} > tempest_variables
echo ${ICONTROL_IPADDR} >> tempest_variables
echo ${OS_AUTH_URL} >> tempest_variables
echo ${OS_AUTH_URL_V3} >> tempest_variables
echo ${PUBLIC_ROUTER_ID} >> tempest_variables
echo ${PUBLIC_NETWORK_ID} >> tempest_variables
echo ${OS_TENANT_ID} >> tempest_variables
echo ${IMAGE_REF} >> tempest_variables

. ./tempest_variables &&

sudo pip install --upgrade git+https://github.com/zancas/prodactivity.git@v0.1.0
sudo publish_test_container tempest f5-openstack-lbaasv2-driver ${BRANCH} ${SUBJECTCODE_ID} ${USER}
REGDIR=`python -c 'import os, prodactivity;print(\\
            os.path.dirname(os.path.abspath(prodactivity.__file__)))'`
REGFILE=${REGDIR}/testrunners/registry_fullname
echo ${REGFILE}
mv ${REGFILE} ./
