// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.opennlp;

import com.google.common.base.Joiner;
import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.postag.POSModel;
import opennlp.tools.postag.POSTaggerME;
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.util.ArrayList;

/**
 * Py4J gateway to POS tagger.
 */
public class PosTaggerGateway {
    POSTaggerME tagger;
    private Joiner whitespaceJoiner;

    public PosTaggerGateway(String modelFilename) {
        // Load model
        POSModel model = new POSModelLoader().load(new File(modelFilename));
        tagger = new POSTaggerME(model);
        whitespaceJoiner = Joiner.on(' ');
    }

    /**
     * POS tag an array of sentences. Assumed to be tokenized already, so that they can be split on
     * spaces.
     *
     * @param sentences input sentences
     * @return array of POS tagged sentences
     */
    public String[] posTag(ArrayList sentences) {
        String[] result = new String[sentences.size()];
        String[] words, tags;

        for (int i = 0; i < sentences.size(); i++) {
            words = ((String)sentences.get(i)).split(" ");
            // POS tag the words
            tags = tagger.tag(words);
            // Put them back together, separated by spaces
            result[i] = whitespaceJoiner.join(tags);
        }
        return result;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Tokenize");
        argParser.description("Run the OpenNLP tokenizer and sentence detector, providing access to it via Py4J");
        argParser.addArgument("model").help("POS tagger model");
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

        // Load the gateway instance
        PosTaggerGateway entryPoint = new PosTaggerGateway(opts.getString("model"));
        // Run the gateway
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
