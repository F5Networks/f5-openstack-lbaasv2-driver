#!/usr/bin/env bash

set -x
set -e

echo "Building docs and Checking links with Sphinx"
make -C docs html
make -C docs linkcheck

echo "Checking grammar and style"
write-good `find ./docs -not \( -path ./docs/drafts -prune \) -name '*.rst'` --passive --so --no-illusion --thereIs --cliches