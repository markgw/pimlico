#!/usr/bin/env bash
# Get the directory containing this script, following any symlinks
# Usual Bash solutions don't work across Max and Linux, so this Perl alternative is better
THIS=$(perl -MCwd -le 'print Cwd::abs_path(shift)' "${BASH_SOURCE[0]}")
DIR=$(dirname $THIS)

# In the same directory as this script, in the Pimlico codebase, lives a Python wrapper script
# This ensures the virtualenv is set up, prepares it if not, then calls Python through the virtualenv
$DIR/python -m pimlico.cli.main $*
