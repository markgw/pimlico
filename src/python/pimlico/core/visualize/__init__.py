"""Visualization of pipelines using Graphviz.

This is not fully implemented yet. In fact, I've barely started. But you'll find some indication of where
I'm going with it on the :doc:`/plans/wishlist`.

.. note::

   Do not import anything from subpackages unless you're doing graph visualization, as they will trigger
   a check for Graphviz and try to install it.

.. note::

   A bug in pygraphviz means that automatic installation on Ubuntu (and perhaps other systems) gets in a
   twist and leaves an unresolved dependency. If you have this problem and system-wide install is an option,
   just install with `sudo apt-get install python-pygraphviz`.

"""
from __future__ import print_function
import sys

from pimlico.core.dependencies.base import check_and_install
from .deps import pygraphviz_dependency

# Run this check whenever this package is imported for the first time
if not pygraphviz_dependency.available({}):
    # Tried to import visualize package, but pygraphviz isn't installed
    print("Tried to import visualization package, but PyGraphviz isn't installed")
    # PyGraphviz isn't available, but if Graphviz is we can install pgv locally
    uninstallable = check_and_install([pygraphviz_dependency], {})
    if uninstallable or not pygraphviz_dependency.available({}):
        print("Could not install PyGraphviz, so cannot continue to import visualization routines")
        sys.exit(1)
