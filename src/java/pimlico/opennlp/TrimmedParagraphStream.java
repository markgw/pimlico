package pimlico.opennlp;

import opennlp.tools.util.ObjectStream;
import opennlp.tools.util.ParagraphStream;

import java.io.IOException;

/**
 * Created by mtw29 on 02/05/14.
 */
public class TrimmedParagraphStream extends ParagraphStream {
    public TrimmedParagraphStream(ObjectStream<String> lineStream) {
        super(lineStream);
    }

    public String read() throws IOException {
        StringBuilder paragraph = new StringBuilder();

        while (true) {
            String line = samples.read();

            // The last paragraph in the input might not
            // be terminated well with a new line at the end.
            if (line == null || line.trim().equals("")) {
                if (paragraph.length() > 0) {
                    return paragraph.toString();
                }
            } else {
                paragraph.append(line.trim()).append(" \n");
            }

            if (line == null)
                return null;
        }
    }
}
