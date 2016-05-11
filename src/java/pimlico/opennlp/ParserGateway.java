// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.opennlp;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.cmdline.parser.ParserTool;
import opennlp.tools.parser.Parse;
import opennlp.tools.parser.Parser;
import opennlp.tools.parser.ParserFactory;
import opennlp.tools.parser.ParserModel;
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * Wrapper around OpenNLP's parser tool to provide access to it via Py4J for Pimlico module.
 */
public class ParserGateway {
    private Parser parser;

    public ParserGateway(File modelPath) throws ModelLoadError {
        InputStream modelIn = null;
        try {
            // Load the parsing model
            modelIn = new FileInputStream(modelPath);
            ParserModel model = new ParserModel(modelIn);
            // Prepare a parser using the model
            parser = ParserFactory.create(model);
        } catch (IOException e) {
            throw new ModelLoadError("could not load parser model: " + e.getMessage());
        } finally {
            if (modelIn != null) {
                try {
                    modelIn.close();
                } catch (IOException e) {}
            }
        }
    }

    public static class ModelLoadError extends Exception {
        public ModelLoadError(String message) {
            super(message);
        }
    }

    public Parse parse(String sentence) {
        // Run the parser to get max 1 parse
        Parse[] parses = ParserTool.parseLine(sentence, parser, 1);
        // Return the parse if we got one
        if (parses.length > 0) {
            return parses[0];
        } else {
            return null;
        }
    }

    public String parseTree(String sentence) {
        Parse parserOutput = parse(sentence);
        // Format the parser output as a PTB tree
        StringBuffer sb = new StringBuffer();
        parserOutput.show(sb);
        return sb.toString();
    }

    public List<Parse> parse(List<String> sentences) {
        ArrayList<Parse> results = new ArrayList<Parse>();
        for (String sentence : sentences)
            results.add(parse(sentence));
        return results;
    }

    public List<String> parseTrees(List<String> sentences) {
        ArrayList<String> results = new ArrayList<String>();
        for (String sentence : sentences)
            results.add(parseTree(sentence));
        return results;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Parser");
        argParser.description("Run the OpenNLP parser, providing access to it via Py4J");
        argParser.addArgument("model_path").help("Path to path model file");
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

        String parserModelPath = opts.getString("model_path");

        // Load the gateway instance
        ParserGateway entryPoint = null;
        try {
            entryPoint = new ParserGateway(new File(parserModelPath));
        } catch (ModelLoadError modelLoadError) {
            modelLoadError.printStackTrace();
            System.exit(1);
        }
        // Create a gateway server, using this as an entry point
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
