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
import opennlp.tools.util.PlainTextByLineStream;

import java.io.*;

/**
 * Tokenization and sentence detection on a stream.
 */
public class Tokenize {
    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Tokenize");
        argParser.description("Run the OpenNLP tokenizer and sentence detector, potentially taking many inputs from " +
                "stdin and outputting to different files. By default, outputs to stdout. On receiving an input paragraph " +
                "'%% OUTPUT: <filename>', starts sending output to <filename>");
        argParser.addArgument("sent-model").help("Sentence detection model");
        argParser.addArgument("tok-model").help("Tokenization model");
        argParser.addArgument("--progress").help("Output this string (without a linebreak, unless given) to stderr " +
                "between each processed file");

        Namespace opts = null;
        try {
            opts = argParser.parseArgs(args);
        } catch (ArgumentParserException e) {
            System.err.println("Error in command-line arguments: " + e);
            System.exit(1);
        }

        String sentModelFilename = opts.getString("sent-model");
        String tokModelFilename = opts.getString("tok-model");
        String progress = opts.getString("progress");

        // Load models
        SentenceModel sentenceModel = new SentenceModelLoader().load(new File(sentModelFilename));
        SentenceDetectorME sentenceDetector = new SentenceDetectorME(sentenceModel);
        TokenizerModel tokenizerModel = new TokenizerModelLoader().load(new File(tokModelFilename));
        Tokenizer tokenizer = new TokenizerME(tokenizerModel);

        // Get input from stdin
        ObjectStream<String> paraStream =
                new TrimmedParagraphStream(new PlainTextByLineStream(new InputStreamReader(System.in)));

        // Start by outputting to stdout
        BufferedWriter outFile = new BufferedWriter(new OutputStreamWriter(System.out));
        StringBuffer sb;
        Joiner whitespaceJoiner = Joiner.on(' ');
        try {
            try {
                String par;
                while ((par = paraStream.read()) != null) {
                    // Check for an '%% OUTPUT:' line, to change the output file
                    if (par.startsWith("%% OUTPUT:")) {
                        String newOutFilename = par.substring(10).trim();
                        // Close the old output file
                        outFile.close();
                        // Open a new one in its place
                        outFile = new BufferedWriter(new FileWriter(newOutFilename));

                        // Output the progress string
                        if (progress != null)
                            System.err.print(progress);
                    } else if (par.length() == 0) {
                        // Empty input gives empty output
                        outFile.write("\n");
                    } else {
                        // Process the paragraph
                        // Sentence detection
                        String[] sents = sentenceDetector.sentDetect(par);

                        // Tokenization
                        for (String sentence : sents) {
                            String[] tokens = tokenizer.tokenize(sentence);
                            // Output the space-separated tokens
                            outFile.write(whitespaceJoiner.join(tokens) + "\n");
                        }
                    }
                }
            } finally {
                // Close the last opened file at the end
                outFile.close();
            }
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
