# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import json

import os

from pimlico.datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter


class NumericResult(PimlicoDatatype):
    """
    Simple datatype to contain a numeric value and a label, representing the result of some process, such as
    evaluation of a model on a task.

    For example, allows results to be plotted by passing them into a graph plotting module.

    """
    datatype_name = "numeric_result"

    def __init__(self, base_dir, pipeline, **kwargs):
        super(NumericResult, self).__init__(base_dir, pipeline, **kwargs)
        self._data_cache = None

    def _read_data(self):
        """ Reads in the data from a file. """
        with open(os.path.join(self.data_dir, "data.json"), "r") as f:
            self._data_cache = json.load(f)

    @property
    def data(self):
        """Raw JSON data"""
        if self._data_cache is None:
            self._read_data()
        return self._data_cache

    @property
    def result(self):
        """The numeric result being stored"""
        return self.data["result"]

    @property
    def label(self):
        """A label to identify this result (e.g. model name)"""
        return self.data["label"]


class NumericResultWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(NumericResultWriter, self).__init__(base_dir, **kwargs)
        self.result = None
        self.label = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(NumericResultWriter, self).__exit__(exc_type, exc_val, exc_tb)
        with open(os.path.join(self.data_dir, "data.json"), "w") as f:
            json.dump({
                "result": self.result,
                "label": self.label,
            }, f)
