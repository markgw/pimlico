# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from future import standard_library
standard_library.install_aliases()
from builtins import object

from queue import Queue, Empty
from threading import Thread


def qget(queue, *args, **kwargs):
    """
    Wrapper that calls the get() method of a queue, catching EINTR interrupts and retrying. Recent versions
    of Python have this built in, but with earlier versions you can end up having processes die while waiting
    on queue output because an EINTR has received (which isn't necessarily a problem).

    :param queue:
    :param args: args to pass to queue's get()
    :param kwargs: kwargs to pass to queue's get()
    :return:
    """
    while True:
        try:
            return queue.get(*args, **kwargs)
        except IOError as e:
            if e.errno == 4:
                # Got an EINTR: try getting again
                continue
            raise


def _enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


class OutputQueue(object):
    """
    Direct a readable output (e.g. pipe from a subprocess) to a queue. Returns the queue.
    Output is added to the queue one line at a time.
    To perform a non-blocking read call get_nowait() or get(timeout=T)
    """
    def __init__(self, out):
        self.out = out
        self.q = Queue()
        t = Thread(target=_enqueue_output, args=(out, self.q))
        t.daemon = True # thread dies with the program
        t.start()

    def get_nowait(self):
        try:
            return self.q.get_nowait()
        except Empty:
            # No more in queue
            return None

    def get(self, timeout=None):
        try:
            return self.q.get(timeout=timeout)
        except Empty:
            return None

    def get_available(self):
        """
        Don't block. Just return everything that's available in the queue.
        """
        lines = []
        try:
            while True:
                lines.append(self.q.get_nowait())
        except Empty:
            pass
        return "\n".join(reversed(lines))
