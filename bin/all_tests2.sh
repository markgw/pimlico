#!/usr/bin/env bash
# Python 2 tests
DIR="$(cd "$( dirname $( readlink -f "${BASH_SOURCE[0]}" ))" && pwd )"
PYTHON_CMD=python2 VIRTUALENV=$DIR/../lib/test_env2 $DIR/python -m unittest discover $DIR/../src/test/python/ "*.py"
