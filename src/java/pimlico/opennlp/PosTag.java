package pimlico.opennlp;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.cmdline.postag.POSModelLoader;
import opennlp.tools.postag.POSModel;
import opennlp.tools.postag.POSTaggerME;
import opennlp.tools.util.ObjectStream;
import opennlp.tools.util.PlainTextByLineStream;

import java.io.*;

/**
 * CLI to OpenNLP's tagger, allowing many taggings to be performed without incurring the large
 * startup cost each time.
 *
 */
public class PosTag {
    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Parse");
        argParser.description("Run the OpenNLP tagger, potentially taking many inputs from stdin and outputting to " +
                "different files. By default, outputs to stdout. On receiving an input line '%% OUTPUT: <filename>', " +
                "starts sending output to <filename>");
        argParser.addArgument("model");

        Namespace opts = null;
        try {
            opts = argParser.parseArgs(args);
        } catch (ArgumentParserException e) {
            System.err.println("Error in command-line arguments: " + e);
            System.exit(1);
        }

        String modelFilename = opts.getString("model");

        // Load a parsing model
        POSModel model = new POSModelLoader().load(new File(modelFilename));
        POSTaggerME tagger = new POSTaggerME(model);

        // Get input from stdin
        ObjectStream<String> lineStream = new PlainTextByLineStream(new InputStreamReader(System.in));

        // Start by outputting to stdout
        BufferedWriter outFile = new BufferedWriter(new OutputStreamWriter(System.out));
        StringBuffer sb;
        String[] words, tags;
        try {
            try {
                String line;
                while ((line = lineStream.read()) != null) {
                    // Check for an '%% OUTPUT:' line, to change the output file
                    if (line.startsWith("%% OUTPUT:")) {
                        String newOutFilename = line.substring(10).trim();
                        // Close the old output file
                        outFile.close();
                        // Open a new one in its place
                        outFile = new BufferedWriter(new FileWriter(newOutFilename));
                    } else if (line.length() == 0) {
                        // Empty input gives empty output
                        outFile.write("\n");
                    } else {
                        // Get the 1-best parse
                        words = line.split(" ");
                        tags = tagger.tag(words);
                        // Output tags along with original words in the CoNLL format that Malt expects
                        // Leave lemmas blank and repeat the tag for both tag columns
                        for (int wordIndex = 0; wordIndex < tags.length; wordIndex++) {
                            outFile.write(
                                    (wordIndex+1) + "\t" + words[wordIndex] + "\t_\t" + tags[wordIndex] +
                                            "\t" + tags[wordIndex] + "\t_\n"
                            );
                        }
                        // Blank line between sentences
                        outFile.write('\n');
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
