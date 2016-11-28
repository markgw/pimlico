#!/usr/bin/env bash
DIR="$(cd "$( dirname $( readlink -f "${BASH_SOURCE[0]}" ))" && pwd )"
$DIR/python -m unittest discover $DIR/../src/test/python/ "*.py"