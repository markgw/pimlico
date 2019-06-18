# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from __future__ import absolute_import
import logging


def get_console_logger(name, debug=False):
    """
    Convenience function to make it easier to create new loggers.

    :param name: logging system logger name
    :param debug: whether to use DEBUG level. By default, uses INFO
    :return:
    """
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Prepare a logger
    log = logging.getLogger(name)
    log.setLevel(level)

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # If coloredlogs is available, enable it
    # We don't make this one of Pimlico's core dependencies, but simply allow
    # it to be installed manually on the system and use it if it's there
    try:
        import coloredlogs
    except ImportError:
        # No coloredogs: never mind
        # Check there's a handler and add a stream handler if not
        if not log.handlers:
            # Just log to the console
            sh = logging.StreamHandler()
            sh.setLevel(logging.DEBUG)
            # Put a timestamp on everything
            formatter = logging.Formatter(fmt)
            sh.setFormatter(formatter)

            log.addHandler(sh)
    else:
        coloredlogs.install(
            level=level, log=log, fmt=fmt
        )

    return log
