package pimlico.opennlp;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.cmdline.parser.ParserModelLoader;
import opennlp.tools.cmdline.parser.ParserTool;
import opennlp.tools.parser.AbstractBottomUpParser;
import opennlp.tools.parser.ParserFactory;
import opennlp.tools.parser.ParserModel;
import opennlp.tools.util.ObjectStream;
import opennlp.tools.util.PlainTextByLineStream;

import java.io.*;

/**
 * CLI to OpenNLP's parser, allowing many parses to be performed without incurring the large
 * startup cost each time.
 *
 */
public class Parse {
    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Parse");
        argParser.description("Run the OpenNLP argParser, potentially taking many inputs from stdin and outputting to " +
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
        ParserModel model = new ParserModelLoader().load(new File(modelFilename));
        AbstractBottomUpParser parser = (AbstractBottomUpParser)ParserFactory.create(model);
        // Don't output to stderr on errors
        parser.setErrorReporting(false);

        // Get input from stdin
        ObjectStream<String> lineStream = new PlainTextByLineStream(new InputStreamReader(System.in));

        // Start by outputting to stdout
        BufferedWriter outFile = new BufferedWriter(new OutputStreamWriter(System.out));
        StringBuffer sb;
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
                        opennlp.tools.parser.Parse[] parses = ParserTool.parseLine(line, parser, 1);
                        // If there's no parse, output an empty line
                        if (parses.length == 0)
                            outFile.write("\n");
                        else {
                            // Render the parse tree for output
                            sb = new StringBuffer();
                            parses[0].show(sb);
                            // Output to the file/stdout
                            outFile.write(sb.toString() + "\n");
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
