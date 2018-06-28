# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os

from pimlico.old_datatypes.base import PimlicoDatatypeWriter
from pimlico.old_datatypes.files import File


class RTabSeparatedValuesFile(File):
    """
    Tabular data stored in a TSV file, suitable for reading in using R's `read.delim` function.

    """
    datatype_name = "r_tsv"

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "r_data.tsv")

    def get_detailed_status(self):
        return ["Data path: %s" % self.absolute_path]


class RTabSeparatedValuesFileWriter(PimlicoDatatypeWriter):
    """
    Writer for TSV files suitable for reading with R.

    If `headings` is specified, this is written as the first line of the file, so `headings=TRUE` should
    be used when reading into R.

    Double quotes (") in the fields will be replaced by double-double quotes (""), which R interprets as a
    double quote. Fields containing tabs will be surrounded by normal double quotes.
    When you read the data into R, the default value of `quotes` (") should therefore be fine.
    No escaping is performed on single quotes (').

    """
    def __init__(self, base_dir, headings=None, **kwargs):
        super(RTabSeparatedValuesFileWriter, self).__init__(base_dir, **kwargs)
        self.headings = headings
        self.file = None

        if self.headings is not None:
            self.row_length = len(self.headings)
        else:
            # Don't know row length until we write the first row
            self.row_length = None

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, "r_data.tsv")

    def __enter__(self):
        super(RTabSeparatedValuesFileWriter, self).__enter__()
        # Open the file for writing and write out the first line, if headings have been given
        self.file = open(self.absolute_path, "w")
        self.file.write((u"%s\n" % u"\t".join(self.headings)).encode("utf-8"))
        return self

    def write_row(self, row):
        """
        If elements are not of string type, they will be coerced to a string for writing. If you want to
        format them differently, do it before calling this method and pass in strings.

        """
        if self.row_length is None:
            # Check all future rows have the same length
            self.row_length = len(row)
        elif self.row_length != len(row):
            raise ValueError("row has the wrong number of elements: %d, expected %d" % (len(row), self.row_length))

        if self.file is None:
            raise IOError("cannot write row when file is not open: write_row() should be called within a *with* "
                          "statement")

        row = [unicode(el) for el in row]
        # Escape any quotes in the fields
        row = [el.replace(u'"', u'""') for el in row]
        # Put quotes around any field include a tab
        row = [u'"%s"' % el if "\t" in el else el for el in row]

        self.file.write((u"%s\n" % u"\t".join(row)).encode("utf-8"))

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(RTabSeparatedValuesFileWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            # Close the file we opened
            self.file.close()
            self.file = None
