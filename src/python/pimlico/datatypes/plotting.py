# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import os
import warnings

from past.builtins import execfile

from pimlico.datatypes import NamedFileCollection


class PlotOutput(NamedFileCollection):
    """
    Output from matplotlib plotting.

    Contains the dataset being plotted, a script to build the plot, and the output PDF.

    """
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(PlotOutput, self).__init__(["plot.py", "data.csv", "plot.pdf"], *args, **kwargs)

    class Writer(object):
        """
        Writes out source data, a Python script for the plotting using Matplotlib and
        a PDF of the resulting plot, if the script completes successfully.

        This approach means that a plot is produced immediately, but can easily be tweaked
        and customized for later use elsewhere by copying and editing the Python
        plotting script.

        Use ``writer.write_file("data.csv", text=True)`` to write the source data and
        ``writer.write_file("plot.py", text=True)`` to write the plotting script, which should
        output a file ``plot.pdf``. Then call ``writer.plot()`` to execute the
        script. If this fails, at least the other files are there so the user can
        correct the errors and use them if they want.

        """
        def plot(self):
            """
            Runs the plotting script. Errors are not caught, so if there's a problem in the script they'll be raised.

            """
            # Change working directory to the one containing the script
            cwd = os.getcwd()
            os.chdir(self.data_dir)
            # Execute the python script
            execfile(self.get_absolute_path("plot.py"), locals(), locals())
            # Change working dir back
            os.chdir(cwd)
            # Check that plot.pdf got created
            pdf_path = self.get_absolute_path("plot.pdf")
            if not os.path.exists(pdf_path):
                warnings.warn("tried to run plotting script. Appeared to complete, but output file "
                              "{} was not created".format(pdf_path))
            else:
                self.task_complete("write_plot.pdf")

        @property
        def data_path(self):
            return self.get_absolute_path("data.csv")

        @property
        def code_path(self):
            return self.get_absolute_path("plot.py")

        @property
        def plot_path(self):
            return self.get_absolute_path("plot.pdf")

        def __exit__(self, exc_type, exc_val, exc_tb):
            incomplete = self.incomplete_tasks
            if "write_plot.pdf" in incomplete and "write_plot.py" not in incomplete and "write_data.csv" not in incomplete:
                # plot.pdf has not been written, but source files are available
                self.plot()
            super(PlotOutput.Writer, self).__exit__(exc_type, exc_val, exc_tb)
