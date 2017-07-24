#!/usr/bin/env bash

set -x
set -e

#echo "Downloading project dependencies"
#pip install --user -e . \
#            git+https://github.com/openstack/neutron.git@liberty-eol \
#            git+https://github.com/openstack/neutron-lbaas.git@liberty-eol

#curl -O -L https://github.com/F5Networks/neutron-lbaas/releases/download/v9.1.0/f5.tgz
#tar xvf f5.tgz -C /venv/lib/python2.7/dist-packages/neutron_lbaas/drivers/

echo "Building docs and Checking links with Sphinx"
make -C docs html
make -C docs linkcheck

echo "Checking grammar and style"
write-good `find ./docs -not \( -path ./docs/drafts -prune \) -name '*.rst'` --passive --so --no-illusion --thereIs --cliches