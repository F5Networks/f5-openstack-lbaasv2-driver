#!/usr/bin/env bash

html="make -C docs html"
linkcheck=$(make -C docs linkcheck | grep 'broken')
grammar="write-good `find ./docs -not \( -path ./docs/drafts -prune \) -name '*.rst'` --passive --so --no-illusion --thereIs --cliches"

if [[ $TRAVIS != "" ]]; then
   OUTPUT=$TRAVIS_BUILD_DIR/_build/linkcheck/output.txt
else
   OUTPUT=docs/_build/linkcheck/output.txt
fi

goodjob() {
  printf "%s\n" "$*" >&2

}

echo "Installing project dependencies"
pip install --user -r requirements.docs.txt

set -x
set -e

echo "Building docs with Sphinx"
$html

echo "Checking grammar and style"
$grammar

[[ $grammar = "" ]] || goodjob "CONGRATULATIONS! You are a grammar wizard."

set +e
set +x
echo "Checking links"
if [[ $linkcheck == "" ]]; then
   echo "Linkcheck succeeded"
else
   echo "WARNING: linkcheck failed. Fix the following broken links:"
   grep 'broken' $OUTPUT
fi
