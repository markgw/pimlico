from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import MultipleInputs
from pimlico.datatypes.plotting import PlotOutput
from pimlico.datatypes.results import NumericResult
from pimlico.modules.visualization import matplotlib_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "bar_chart"
    module_readable_name = "Bar chart plotter"
    module_inputs = [("values", MultipleInputs(NumericResult))]
    module_outputs = [("plot", PlotOutput)]

    def get_software_dependencies(self):
        return [matplotlib_dependency]
