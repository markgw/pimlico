# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.dependencies.base import SystemCommandDependency
from pimlico.core.dependencies.python import PythonPackageOnPip


class GraphvizDependency(SystemCommandDependency):
    def __init__(self, **kwargs):
        super(GraphvizDependency, self).__init__("Graphviz", "dot -V", **kwargs)

    def installation_instructions(self):
        return """\
Install Graphviz on your system using a package manager, or by following the instructions to
compile from source at:
  http://www.graphviz.org/Download.php

For example, on Ubuntu you can run:
  sudo apt-get install graphviz

"""

pygraphviz_dependency = PythonPackageOnPip("pygraphviz", name="PyGraphviz", dependencies=[GraphvizDependency()])
