package pimlico.core;

import opennlp.tools.util.ObjectStream;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.Reader;
import java.util.Arrays;

/**
 * Mirror of a StreamCommunicationPacket on the Python side.
 */
public class StreamCommunicationPacketReader implements ObjectStream<String> {
    private BufferedReader in;

    public StreamCommunicationPacketReader(Reader in) {
        this.in = new BufferedReader(in);
    }

    @Override
    public String read() throws IOException {
        // Read the header
        char[] cbuf = new char[16];
        int read = 0;
        // Keep reading until we've got 16 chars
        while (read < 16)
            read += in.read(cbuf, read, 16-read);
        int dataLength = Integer.parseInt(new String(Arrays.copyOfRange(cbuf, 7, 13)));

        // Read the data for the packet
        read = 0;
        cbuf = new char[dataLength];
        while (read < dataLength)
            read += in.read(cbuf, read, dataLength - read);

        return new String(cbuf);
    }

    @Override
    public void reset() throws IOException, UnsupportedOperationException {
        in.reset();
    }

    @Override
    public void close() throws IOException {
        in.close();
    }
}
