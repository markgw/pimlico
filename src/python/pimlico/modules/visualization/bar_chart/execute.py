# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from future import standard_library
standard_library.install_aliases()
from builtins import zip, str

import os
import csv
from io import StringIO

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # Get values and labels from the inputs
        self.log.info("Collecting data")
        inputs = self.info.get_input("results", always_list=True)
        labels = [result.label for result in inputs]
        values = [result.value for result in inputs]

        self.log.info("Outputting data and plotting code")
        with self.info.get_output_writer("plot") as writer:
            # Prepare data to go to CSV file
            sio = StringIO()
            csv_writer = csv.writer(sio)
            for label, value in zip(labels, values):
                csv_writer.writerow([str(label), str(value)])
            writer.write_file("data.csv", sio.getvalue(), text=True)

            # Use a standard template plot python file
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "plot_template.py"), "r") as f:
                plotting_code = f.read()
            # Remove the first line, which is a comment to explain what the file is
            plotting_code = "\n".join(plotting_code.splitlines()[1:])
            # Otherwise, the script stays exactly as it is
            writer.write_file("plot.py", plotting_code, text=True)

            # Written the plot code and data
            # Now do the plotting
            self.log.info("Running plotter")
            writer.plot()

            self.log.info("Plot output to {}".format(writer.plot_path))
            self.log.info("Customize plot by editing {} and recompiling: python plot.py".format(writer.code_path))
