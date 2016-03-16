

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
