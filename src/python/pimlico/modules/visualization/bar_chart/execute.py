# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from future import standard_library
from pimlico.core.modules.execute import ModuleExecutionError

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
        labels = [result.label if result is not None else "unavailable" for result in inputs]
        values = [result.value if result is not None else 0. for result in inputs]

        opts = self.info.options
        if opts["labels"] is not None and len(opts["labels"]) > 0:
            if len(opts["labels"]) != len(values):
                raise ModuleExecutionError("bar chart plotter got {} labels, but {} input values".format(
                    len(opts["labels"]), len(values)
                ))
            labels = opts["labels"]

        colors = opts["colors"] or ['g', 'b', 'y', 'm', 'c', '#B1C7CA', '#90F0A0']

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
            # Replace any variables
            plotting_code = plotting_code.format(colors=", ".join("'{}'".format(c) for c in colors))
            # Otherwise, the script stays exactly as it is
            writer.write_file("plot.py", plotting_code, text=True)

            # Written the plot code and data
            # Now do the plotting
            self.log.info("Running plotter")
            writer.plot()

            self.log.info("Plot output to {}".format(writer.plot_path))
            self.log.info("Customize plot by editing {} and recompiling: python plot.py".format(writer.code_path))
