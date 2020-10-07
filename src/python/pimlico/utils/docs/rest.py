# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import zip
from builtins import range
from sphinx.util import rst


def make_table(grid, header=None):
    all_rows = [header] + grid if header is not None else grid
    col_widths = [max(len(row[i]) for row in all_rows) for i in range(len(all_rows[0]))]
    rst = table_div(col_widths, 0)

    if header is not None:
        # Produce a header row
        rst = rst + "| " + " | ".join([normalize_cell(x, width) for (x, width) in zip(header, col_widths)]) + " |\n"
        rst = rst + table_div(col_widths, True)

    for row in grid:
        rst = rst + "| " + " | ".join([normalize_cell(x, width) for (x, width) in zip(row, col_widths)]) + " |\n"
        rst = rst + table_div(col_widths)
    return rst


def table_div(col_widths, header_flag=False):
    if header_flag:
        return "+%s+\n" % "+".join((col_width+2)*"=" for col_width in col_widths)
    else:
        return "+%s+\n" % "+".join((col_width+2)*"-" for col_width in col_widths)


def normalize_cell(string, length):
    return string + ((length - len(string)) * " ")


def format_heading(level, text, escape=True):
    """Create a heading of <level> [1, 2 or 3 supported]."""
    if escape:
        text = rst.escape(text)
    underlining = ['=', '-', '~', ][level - 1] * len(text)
    return '%s\n%s\n\n' % (text, underlining)
