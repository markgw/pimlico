# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Simple plotting of a bar chart from numeric data using Matplotlib

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.base import MultipleInputs
from pimlico.old_datatypes.plotting import PlotOutput
from pimlico.old_datatypes.results import NumericResult
from pimlico.modules.visualization import matplotlib_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "bar_chart"
    module_readable_name = "Bar chart plotter"
    module_inputs = [("values", MultipleInputs(NumericResult))]
    module_outputs = [("plot", PlotOutput)]
    module_supports_python2 = True

    def get_software_dependencies(self):
        return [matplotlib_dependency]
