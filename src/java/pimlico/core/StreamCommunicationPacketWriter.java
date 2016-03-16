package pimlico.core;

import java.io.IOException;
import java.io.Writer;
import java.nio.charset.Charset;
import java.util.Arrays;

public class StreamCommunicationPacketWriter extends Writer {
    private Writer out;

    public StreamCommunicationPacketWriter(Writer out) {
        this.out = out;
    }

    @Override
    public void write(char[] chars, int off, int len) throws IOException {
        // Pull out the substring
        char[] data = Arrays.copyOfRange(chars, off, off + len);
        String stringData = new String(data);
        // UTF-8 encode the data
        // We're not actually able to use this to pass on to the writer, but it tells us how long the data will
        // be when encoded for sending
        int dataLength = Charset.forName("UTF-8").encode(stringData).array().length;
        // Prepare the header, giving the length of the data
        String header = String.format("PACKET(%06d): ", dataLength);
        // Send the data to the underlying stream
        out.write(header + stringData);
    }

    @Override
    public void flush() throws IOException {
        out.flush();
    }

    @Override
    public void close() throws IOException {
        out.close();
    }
}
