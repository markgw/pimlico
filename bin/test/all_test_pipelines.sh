#!/usr/bin/env bash
THIS=$(perl -MCwd -le 'print Cwd::abs_path(shift)' "${BASH_SOURCE[0]}")
DIR=$(dirname $THIS)

VIRTUALENV=$DIR/../../lib/test_env $DIR/../python -m pimlico.test.suite $DIR/../../test/suites/all.csv $*
