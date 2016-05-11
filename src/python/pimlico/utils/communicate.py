# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from contextlib import contextmanager
from threading import Timer


@contextmanager
def timeout_process(proc, timeout):
    """
    Context manager for use in a `with` statement. If the with block hasn't completed after the given number
    of seconds, the process is killed.

    :param proc: process to kill if timeout is reached before end of block
    :return:
    """
    timer = Timer(timeout, proc.kill)
    # Set a timer going
    timer.start()
    # Continue executing the with block
    try:
        yield timer
    finally:
        # Cancel the timer now, if it's still running
        timer.cancel()


class StreamCommunicationPacket(object):
    def __init__(self, data):
        self.data = unicode(data)

    @property
    def length(self):
        return len(self.data.encode("utf-8"))

    def encode(self):
        length = "%06d" % self.length
        if len(length) > 6:
            raise ValueError("StreamCommunicationPacket can't handle data packets longer than 1M chars")

        return "PACKET(%s): %s" % (length, self.data.encode("utf-8"))

    @staticmethod
    def read(stream):
        header = stream.read(16)
        if not header.startswith("PACKET("):
            raise StreamCommunicationError("expected header at start of stream, but got %s" % header)

        # The next part, always 6 chars, is the length of the packet
        length = int(header[7:13])
        # Read this length of bytes from the stream
        data = stream.read(length)
        return StreamCommunicationPacket(data.decode("utf-8"))


class StreamCommunicationError(Exception):
    pass
