# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html


from builtins import zip
from builtins import range
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
