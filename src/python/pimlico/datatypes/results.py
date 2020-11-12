# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import json
import os

from pimlico.datatypes.base import PimlicoDatatype
from pimlico.utils.core import cached_property


class NumericResult(PimlicoDatatype):
    """
    Simple datatype to contain a numeric value and a label, representing
    the result of some process, such as evaluation of a model on a task.

    Write using ``writer.write(label, value)``. The label must be a string,
    identifying what the result is, e.g. "f-score". The value can be any
    JSON-serializable type, e.g. int or float.

    For example, allows results to be plotted by passing them into a graph plotting module.

    """
    datatype_name = "numeric_result"
    datatype_supports_python2 = True

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["data.json"]

        @cached_property
        def data(self):
            with open(os.path.join(self.data_dir, "data.json"), "r") as f:
                return json.load(f)

        @cached_property
        def label(self):
            return self.data["label"]

        @cached_property
        def value(self):
            return self.data["value"]

    class Writer(object):
        required_tasks = ["data"]

        def write(self, label, value):
            # Write out the data JSON file
            with open(os.path.join(self.data_dir, "data.json"), "w") as f:
                json.dump({"label": label, "value": value}, f)
            self.task_complete("data")
