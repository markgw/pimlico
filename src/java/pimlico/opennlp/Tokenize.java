package pimlico.opennlp;

import com.google.common.base.Joiner;
import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.sentdetect.SentenceDetectorME;
import opennlp.tools.sentdetect.SentenceModel;
import opennlp.tools.tokenize.Tokenizer;
import opennlp.tools.tokenize.TokenizerME;
import opennlp.tools.tokenize.TokenizerModel;
import opennlp.tools.util.ObjectStream;
import pimlico.core.StreamCommunicationPacketReader;
import pimlico.core.StreamCommunicationPacketWriter;

import java.io.*;
import java.sql.DriverManager;
import java.util.ArrayList;
import java.util.List;

/**
 * Tokenization and sentence detection on a stream.
 */
public class Tokenize {
    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Tokenize");
        argParser.description("Run the OpenNLP tokenizer and sentence detector, potentially taking many inputs from " +
                "stdin and outputting to different files. Outputs to stdout");
        argParser.addArgument("sent_model").help("Sentence detection model").required(true);
        argParser.addArgument("tok_model").help("Tokenization model").required(true);

        Namespace opts = null;
        try {
            opts = argParser.parseArgs(args);
        } catch (ArgumentParserException e) {
            System.err.println("Error in command-line arguments: " + e);
            System.exit(1);
        }

        String sentModelFilename = opts.getString("sent_model");
        String tokModelFilename = opts.getString("tok_model");

        // Load models
        SentenceModel sentenceModel = new SentenceModelLoader().load(new File(sentModelFilename));
        SentenceDetectorME sentenceDetector = new SentenceDetectorME(sentenceModel);
        TokenizerModel tokenizerModel = new TokenizerModelLoader().load(new File(tokModelFilename));
        Tokenizer tokenizer = new TokenizerME(tokenizerModel);

        // Get input from stdin
        ObjectStream<String> paraStream =
                new TrimmedParagraphStream(new StreamCommunicationPacketReader(new InputStreamReader(System.in)));

        // Outputting to stdout
        StreamCommunicationPacketWriter outStream = new StreamCommunicationPacketWriter(
                new BufferedWriter(new OutputStreamWriter(System.out))
        );
        StringBuffer sb;
        Joiner whitespaceJoiner = Joiner.on(' ');
        Joiner lineJoiner = Joiner.on('\n');
        try {
            try {
                String par;
                while ((par = paraStream.read()) != null) {
                    if (par.length() == 0) {
                        // Empty input gives empty output
                        outStream.write("");
                    } else {
                        // Process the paragraph
                        // Sentence detection
                        String[] sents = sentenceDetector.sentDetect(par);

                        // Tokenization
                        List<String> tokenizedSents = new ArrayList<String>();
                        for (String sentence : sents) {
                            String[] tokens = tokenizer.tokenize(sentence);
                            // Output the space-separated tokens
                            tokenizedSents.add(whitespaceJoiner.join(tokens));
                        }
                        // Sent the final text to the stream
                        outStream.write(lineJoiner.join(tokenizedSents));
                    }
                }
            } finally {
                // Close the last opened file at the end
                outStream.close();
            }
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
