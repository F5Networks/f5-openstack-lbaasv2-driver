#!/bin/bash -ex

SRC_DIR=$1
DIST_DIR=$2
OS_VERSION=6

DEST_DIR="${SRC_DIR}/${DIST_DIR}"

echo "Building RPM packages...${DIST_DIR}"
buildroot=$(mktemp -d /tmp/f5-openstack-lbaasv2-driver.XXXX)

cp -R $SRC_DIR/* ${buildroot}

pushd ${buildroot}
cp ${DIST_DIR}/MANIFEST.in ${buildroot}

python setup.py bdist_rpm

mkdir -p ${DEST_DIR}/rpms

for pkg in $(ls dist/*.rpm); do
  if [[ $pkg =~ ".noarch." ]]; then
    mv $pkg ${pkg%%.noarch.rpm}.el${OS_VERSION}.noarch.rpm
  fi
done
cp -R dist/*.rpm ${DEST_DIR}/rpms

popd
