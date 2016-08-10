#!/bin/bash

SRC_DIR=$1
VERSION=$2
RELEASE=$3
DISTRO=$4

PKG_NAME="f5-openstack-lbaasv2-driver"
RPM_PKG="${PKG_NAME}-${VERSION}-${RELEASE}.${DISTRO}.noarch.rpm"
DEST_DIR="${SRC_DIR}/${PKG_NAME}-dist/rpms"

pushd "${DEST_DIR}"
rpm -ivh ${RPM_PKG}
if [[ $? != 0 ]]; then
	echo "Install of ${RPM_PKG} failed"
	exit 1
fi

popd
exit 0	
