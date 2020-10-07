// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

package pimlico.malt;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import org.maltparser.concurrent.ConcurrentMaltParserModel;
import org.maltparser.concurrent.ConcurrentMaltParserService;
import org.maltparser.core.exception.MaltChainedException;
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Wrapper around OpenNLP's coreference resolution tool to provide access to it via Py4J for Pimlico module.
 */
public class ParserGateway {
    private final ConcurrentMaltParserModel model;

    public ParserGateway(ConcurrentMaltParserModel model) {
        this.model = model;
    }

    /**
     * Take in an array of tokens, where each one is a row of CoNLL-format data and annotate with dependency
     * parse, returning the CoNLL-format parsed sentence.
     *
     * Thread-safe (provided Malt's thread safety holds), so you can call it multiple times concurrently
     * through the gateway.
     *
     * @param conllSentence    tokens of input data
     * @return tokens of parsed data
     * @throws MaltChainedException
     */
    public String[] parseFromCoNLL(List<String> conllSentence) throws MaltChainedException {
        // Parse the sentence
        return model.parseTokens(conllSentence.toArray(new String[conllSentence.size()]));
    }

    /**
     * @param conllSentences    sentences of tokens of input data
     * @return tokens of parsed data
     * @throws MaltChainedException
     */
    public List<String[]> parseDocFromCoNLL(List<List<String>> conllSentences) throws MaltChainedException {
        List<String[]> result = new ArrayList<String[]>();
        // Parse each sentence
        for (List<String> conllSentence : conllSentences)
            result.add(parseFromCoNLL(conllSentence));
        return result;
    }

    /**
     * Version of parse interface that takes a whole doc as input, with blank lines between sentences and one
     * token per line.
     */
    public List<String[]> parseDocFromCoNLLString(String conllSentences) throws MaltChainedException {
        List<String[]> result = new ArrayList<String[]>();
        // Parse each sentence, separated by blank lines
        for (String conllSentence : conllSentences.split("\n\n")) {
            // Split up the lines (tokens) of the sentence
            result.add(parseFromCoNLL(Arrays.asList(conllSentence.split("\n"))));
        }
        return result;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Malt parser");
        argParser.description("Run the Malt parser, providing access to it via Py4J");
        argParser.addArgument("model_file").help("Path to Malt model file");
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

        ConcurrentMaltParserModel model;
        try {
            URL modelURL = new File(opts.getString("model_file")).toURI().toURL();
            model = ConcurrentMaltParserService.initializeParserModel(modelURL);

            // Load the gateway instance
            ParserGateway entryPoint = new ParserGateway(model);
            // Create a gateway server, using this as an entry point
            Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
        } catch (Exception e) {
            System.err.println("Error starting up Malt parser gateway");
            e.printStackTrace();
            System.exit(1);
        }
    }
}
