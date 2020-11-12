# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Simple plotting of a bar chart from numeric results data using Matplotlib.

"""
from pimlico.core.modules.options import comma_separated_strings

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import MultipleInputs
from pimlico.datatypes.plotting import PlotOutput
from pimlico.datatypes.results import NumericResult
from pimlico.modules.visualization import matplotlib_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "bar_chart"
    module_readable_name = "Bar chart plotter"
    module_inputs = [("results", MultipleInputs(NumericResult()))]
    module_outputs = [("plot", PlotOutput())]
    module_supports_python2 = True
    module_options = {
        "labels": {
            "help": "If given, a list of labels corresponding to the inputs to use in plots. "
                    "Otherwise, inputs are numbered and the labels provided in their label fields are used",
            "type": comma_separated_strings,
        },
        "colors": {
            "help": "Pyplot colors to use for each series. If shorter than the number of inputs, "
                    "cycles round. Specify according to pyplot docs: https://matplotlib.org/2.0.2/api/colors_api.html. "
                    "E.g. use single-letter color names, HTML color codes or HTML color names",
            "type": comma_separated_strings,
            "default": ["r", "g", "b", "y", "c", "m", "k"],
        },
    }

    def get_software_dependencies(self):
        return [matplotlib_dependency]
