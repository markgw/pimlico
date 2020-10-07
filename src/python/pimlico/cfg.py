# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Global config

Various global variables. Access as follows:

   from pimlico import cfg

   # Set global config parameter
   cfg.parameter = "Value"
   # Use parameter
   print cfg.parameter

There are some global variables in ``pimlico`` (in the __init__.py) that probably should be
moved here, but I'm leaving them for now. At the moment, none of those are ever written from
outside that file (i.e. think of them as constants, rather than config), so the only reason
to move them is to keep everything in one place.

"""
import os

# By default, we run in interative mode, assuming the user's at a terminal
# This switch tells interface components that they can't expect input from a user
# This should mean, for example, that we don't display progress bars, whose output looks
#  bad when piped to a file
# The parameter can be set using the environment variable PIM_NON_INT to 1,
#  or the cmd line switch --non-interactive
# TODO Add this to the documentation
# TODO Allow this to be set on the cmd line
NON_INTERACTIVE_MODE = len(os.environ.get("PIM_NON_INT", "")) > 0
