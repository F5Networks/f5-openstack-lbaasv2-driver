#!/usr/bin/env bash

set -e
set -x
echo "Installing project dependencies"
pip install --user -r requirements.docs.txt

echo "Building docs with Sphinx"
make -C docs html

echo "Checking grammar and style"
write-good `find ./docs -not \( -path ./docs/drafts -prune \) -name '*.rst'` --passive --so --no-illusion --thereIs --cliches || true

echo "Checking links"
make -C docs linkcheck | grep "broken" || true

