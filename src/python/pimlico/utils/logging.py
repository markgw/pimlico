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

    if not log.handlers:
        # Just log to the console
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        # Put a timestamp on everything
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sh.setFormatter(formatter)

        log.addHandler(sh)

    return log
