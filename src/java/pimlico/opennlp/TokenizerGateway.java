// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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
import pimlico.core.Py4JGatewayStarter;

import java.io.File;

/**
 * Py4J gateway to tokenizer.
 */
public class TokenizerGateway {
    private SentenceDetectorME sentenceDetector;
    private Tokenizer tokenizer;
    private Joiner whitespaceJoiner;

    public TokenizerGateway(File sentModelFile, File tokModelFile) {
        // Load models
        SentenceModel sentenceModel = new SentenceModelLoader().load(sentModelFile);
        sentenceDetector = new SentenceDetectorME(sentenceModel);

        TokenizerModel tokenizerModel = new TokenizerModelLoader().load(tokModelFile);
        tokenizer = new TokenizerME(tokenizerModel);

        whitespaceJoiner = Joiner.on(' ');
    }

    public String[] tokenize(String input) {
        if (input.length() == 0) {
            // Empty input gives empty output
            return new String[] {""};
        } else {
            // Process the paragraph
            // Sentence detection
            String[] sents = sentenceDetector.sentDetect(input);

            // Tokenization
            String[] tokenizedSents = new String[sents.length];
            for (int i=0; i < sents.length; i++) {
                String[] tokens = tokenizer.tokenize(sents[i]);
                // Output the space-separated tokens
                tokenizedSents[i] = whitespaceJoiner.join(tokens);
            }
            return tokenizedSents;
        }
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Tokenize");
        argParser.description("Run the OpenNLP tokenizer and sentence detector, providing access to it via Py4J");
        argParser.addArgument("sent_model").help("Sentence detection model");
        argParser.addArgument("tok_model").help("Tokenization model");
        argParser.addArgument("--port").type(Integer.class).help("Specify a port for gateway server to run on").setDefault(0);
        argParser.addArgument("--python-port").type(Integer.class).help("Specify a port for gateway server to use " +
                "to response to Python").setDefault(0);

        Namespace opts = null;
        try {
            opts = argParser.parseArgs(args);
        } catch (ArgumentParserException e) {
            System.err.println("Error in command-line arguments: " + e);
            System.exit(1);
        }

        String sentModelFilename = opts.getString("sent_model");
        String tokModelFilename = opts.getString("tok_model");

        // Load the gateway instance
        TokenizerGateway entryPoint = new TokenizerGateway(new File(sentModelFilename), new File(tokModelFilename));
        // Create a gateway server, using this as an entry point
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
