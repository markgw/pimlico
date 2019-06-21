# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import zip
from textwrap import wrap


def multiline_tablate(table, widths, **kwargs):
    from tabulate import tabulate
    # Wrap columns
    table = [[wrap(cell, width=width) for (cell, width) in zip(row, widths)] for row in table]
    table_split = []
    for row in table:
        subrows = max(len(cell) for cell in row)
        new_row = [cell + [""] * (subrows - len(cell)) for cell in row]
        table_split.extend(list(zip(*new_row)))
        # Add a blank line
        table_split.append([""] * len(table_split[0]))
    return tabulate(table_split[:-1], **kwargs)


def title_box(title_text):
    """
    Make a nice big pretty title surrounded by a box.
    """
    lines = title_text.splitlines()
    content_width = max(len(line)+2 for line in lines)
    top_border = "+" + "-" * content_width + "+"
    # Centre each of the lines
    lines = [("{:^%d}" % content_width).format(line) for line in lines]
    return "\n".join([top_border] + ["|%s|" % line for line in lines] + [top_border])
