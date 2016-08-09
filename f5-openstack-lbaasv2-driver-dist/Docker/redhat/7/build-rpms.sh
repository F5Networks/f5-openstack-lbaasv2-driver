#!/bin/bash -ex

SRC_DIR=$1
PKG_NAME="f5-openstack-lbaasv2-driver"
DIST_DIR="${PKG_NAME}-dist"
OS_VERSION=7

DEST_DIR="${SRC_DIR}/${DIST_DIR}"

echo "Building RPM packages...${DIST_DIR}"
buildroot=$(mktemp -d /tmp/${PKG_NAME}.XXXX)

cp -R $SRC_DIR/* ${buildroot}

pushd ${buildroot}

python setup.py bdist_rpm

mkdir -p ${DEST_DIR}/rpms

for pkg in $(ls dist/*.rpm); do
  if [[ $pkg =~ ".noarch." ]]; then
    mv $pkg ${pkg%%.noarch.rpm}.el${OS_VERSION}.noarch.rpm
  fi
done
cp -R dist/*.rpm ${DEST_DIR}/rpms

popd
