#!/usr/bin/env bash
# Temporary script to just run unit tests for the Pimarc file format.
# Once development of the readers/writers is finished, this will be removed.
# The tests are run by all_unit_tests.sh anyway.
DIR="$(cd "$( dirname $( readlink -f "${BASH_SOURCE[0]}" ))" && pwd )"
VIRTUALENV=$DIR/../../lib/test_env $DIR/../python -m unittest discover $DIR/../../src/test/python/pimlicotest/utils/pimarc/ "*.py"
