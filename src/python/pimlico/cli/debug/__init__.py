"""Extra-verbose debugging facility

Tools for very slowly and verbosely stepping through the processing that a given module does to debug it.

Enabled using the `--step` switch to the run command.

"""
from __future__ import unicode_literals

import traceback


def fmt_frame_info(info):
    return "Called from %s:%d (%s)" % (info[0], info[1], info[2])


def output_stack_trace(frame=None):
    traceback.print_stack(frame)
