#!/usr/bin/env bash
# Python 2 test pipelines
THIS=$(perl -MCwd -le 'print Cwd::abs_path(shift)' "${BASH_SOURCE[0]}")
DIR=$(dirname $THIS)

PYTHON_CMD=python2 VIRTUALENV=$DIR/../../lib/test_env2 $DIR/../python -m pimlico.test.suite $DIR/../../test/suites/all.csv $*
