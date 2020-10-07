# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import os
import warnings

from pimlico.datatypes import NamedFileCollection
from past.builtins import execfile


class PlotOutput(NamedFileCollection):
    """
    Output from matplotlib plotting.

    Contains the dataset being plotted, a script to build the plot, and the output PDF.

    Also supplies additional datatypes to point to the individual files.

    """
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(PlotOutput, self).__init__(["plot.py", "data.csv", "plot.pdf"], *args, **kwargs)

    class Writer(object):
        def plot(self):
            """
            Runs the plotting script. Errors are not caught, so if there's a problem in the script they'll be raised.

            """
            # Change working directory to the one containing the script
            cwd = os.getcwd()
            os.chdir(self.data_dir)
            # Execute the python script
            execfile(self.get_absolute_path("plot.py"))
            # Change working dir back
            os.chdir(cwd)
            # Check that plot.pdf got created
            pdf_path = self.get_absolute_path("plot.pdf")
            if not os.path.exists(pdf_path):
                warnings.warn("tried to run plotting script. Appeared to complete, but output file "
                              "{} was not created".format(pdf_path))
            else:
                self.task_complete("write_plot.pdf")

        def __exit__(self, exc_type, exc_val, exc_tb):
            incomplete = self.incomplete_tasks
            if "write_plot.pdf" in incomplete and "write_plot.py" not in incomplete and "write_data.csv" not in incomplete:
                # plot.pdf has not been written, but source files are available
                self.plot()
            super(PlotOutput.Writer, self).__exit__(exc_type, exc_val, exc_tb)
