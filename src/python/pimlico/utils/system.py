# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""Lowish-level system operations

"""


def set_proc_title(title):
    """
    Tries to set the current process title. This is very system-dependent and may not always work.

    If it's available, we use the `setproctitle` package, which is the most reliable way to do this.
    If not, we try doing it by loading libc and calling `prctl` ourselves. This is not reliable and only
    works on Unix systems.
    If neither of these works, we give up and return False.

    If you want to increase the chances of this working (e.g. your process titles don't seem to be
    getting set by Pimlico and you'd like them to), try installing `setproctitle`, either system-wide
    or in Pimlico's virtualenv.

    @return: True if the process succeeds, False if there's an error

    """
    try:
        # First try loading setproctitle, the most reliable method
        import setproctitle
    except ImportError:
        # setproctitle not available, try another approach
        try:
            import ctypes
            from ctypes.util import find_library
            libc = ctypes.CDLL(find_library("c"))
            # Operation 15 = set title
            retcode = libc.prctl(15, ctypes.c_char_p(title), 0, 0, 0)
            if retcode:
                return False
        except:
            return False
    else:
        # We've got setproctitle: use that
        try:
            setproctitle.setproctitle(title)
        except:
            return False
    return True
