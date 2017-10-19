# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os

from pimlico.datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter
from pimlico.datatypes.files import NamedFile


class PlotOutput(PimlicoDatatype):
    """
    Output from matplotlib plotting.

    Contains the dataset being plotted, a script to build the plot, and the output PDF.

    Also supplies additional datatypes to point to the individual files.

    """
    supplied_additional = [
        ("pdf", NamedFile("plot.pdf")),
        ("code", NamedFile("plot.py")),
        ("data", NamedFile("data.csv")),
    ]

    @property
    def script_path(self):
        return os.path.join(self.data_dir, "plot.py")

    def plot(self):
        """
        Runs the plotting script. Errors are not caught, so if there's a problem in the script they'll be raised.

        """
        # Change working directory to the one containing the script
        cwd = os.getcwd()
        os.chdir(self.data_dir)
        # Execute the python script
        execfile(self.script_path)
        # Change working dir back
        os.chdir(cwd)

    @property
    def pdf_path(self):
        return os.path.join(self.data_dir, "plot.pdf")

    @property
    def data_path(self):
        return os.path.join(self.data_dir, "data.csv")


class PlotOutputWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir):
        super(PlotOutputWriter, self).__init__(base_dir)
        self.plotting_code = ""
        self.data = ""

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(PlotOutputWriter, self).__exit__(exc_type, exc_val, exc_tb)
        with open(os.path.join(self.data_dir, "data.csv"), "w") as f:
            f.write(self.data)
        with open(os.path.join(self.data_dir, "plot.py"), "w") as f:
            f.write(self.plotting_code)
