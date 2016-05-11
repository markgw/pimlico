# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os
from pimlico import LOG_DIR


def get_log_file(name):
    """
    Returns the path to a log file that may be used to output helpful logging info. Typically used
    to output verbose error information if something goes wrong. The file can be found in the Pimlico
    log dir.

    :param name: identifier to distinguish from other logs
    :return: path
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    return os.path.abspath(os.path.join(LOG_DIR, "%s.log" % name))
