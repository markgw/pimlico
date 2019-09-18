# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Optional dependency on pydot for visualization.

Optional use of pydot based on Keras.

"""

try:
    import pydot
except ImportError:
    pydot = None


def check_pydot():
    """Raise errors if `pydot` or GraphViz unavailable."""
    if pydot is None:
        raise ImportError(
            'Failed to import `pydot`. '
            'Please install `pydot`. '
            'For example with `pip install pydot`.')
    try:
        # Attempt to create an image of a blank graph
        # to check the pydot/graphviz installation.
        pydot.Dot.create(pydot.Dot())
    except OSError:
        raise OSError(
            '`pydot` failed to call GraphViz.'
            'Please install GraphViz (https://www.graphviz.org/) '
            'and ensure that its executables are in the $PATH.')
