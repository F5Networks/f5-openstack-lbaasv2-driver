#!/usr/bin/env bash

set -ex

HEAT_PKG_LOC="git+https://github.com/F5Networks/f5-openstack-heat-plugins.git@${BRANCH}"
PIP_INSTALL_LOC=/usr/lib/python2.7/site-packages/f5_heat
HEAT_PLUGIN_LOC=/usr/lib/heat
HEAT_EXTRA_VARS="remote_user=testlab heat_plugins_pkg_location=${HEAT_PKG_LOC} pip_install_dest=${PIP_INSTALL_LOC} heat_plugin_install_dest=${HEAT_PLUGIN_LOC} heat_engine_service_name=openstack-heat-engine"

sudo -E docker pull docker-registry.pdbld.f5net.com/openstack-test-ansibleserver-prod/mitaka
sudo -E docker run \
    --volumes-from `hostname | xargs` \
docker-registry.pdbld.f5net.com/openstack-test-ansibleserver-prod/mitaka:latest \
/f5-openstack-ansible/playbooks/heat_plugins_deploy.yaml \
--extra-vars "${HEAT_EXTRA_VARS}"
