#!/bin/bash

SRC_DIR=$1
VERSION=$2
RELEASE=$3
DISTRO=$4

PKG_NAME="f5-openstack-lbaasv2-driver"
DEB_PKG="python-${PKG_NAME}_${VERSION}-${RELEASE}_${DISTRO}_all.deb"
DEST_DIR="${SRC_DIR}/${PKG_NAME}-dist/deb_dist"

pushd "${DEST_DIR}"
dpkg -i ${DEB_PKG}
if [[ $? != 0 ]]; then
	echo "Install of ${DEB_PKG} failed"
	exit 1
fi

popd
exit 0	
