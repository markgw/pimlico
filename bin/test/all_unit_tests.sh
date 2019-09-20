#!/usr/bin/env bash
DIR="$(cd "$( dirname $( readlink -f "${BASH_SOURCE[0]}" ))" && pwd )"
VIRTUALENV=$DIR/../../lib/test_env $DIR/../python -m unittest discover $DIR/../../src/test/python/ "*.py"
