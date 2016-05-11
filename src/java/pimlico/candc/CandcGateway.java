// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.candc;

import cat_combination.RuleInstancesParams;
import chart_parser.ChartParser;
import chart_parser.ViterbiDecoder;
import io.Params;
import model.Lexicon;
import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import pimlico.core.Py4JGatewayStarter;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Wrapper around the new Java C&C to provide access to it via Py4J for Pimlico module.
 * Based on Parser class.
 */
public class CandcGateway {
    PrintWriter log;
    ChartParser parser;
    ViterbiDecoder viterbiDecoder;

    public CandcGateway(String weightsFile, String paramsFile, String grammarDir, String lexiconFile, String featuresFile)
            throws CandcStartupException {
        // Parameters where the defaults (set for the beam parser) need changing for the Viterbi parser
        Params.MAX_SUPERCATS = 1000000;
        Params.newFeatures = false;
        Params.betas = new double[] { 0.075, 0.03, 0.01, 0.001 };

        boolean oracleFscore = false;
        boolean seenRules = true;
        RuleInstancesParams ruleInstancesParams = new RuleInstancesParams(seenRules, false, false, false, false, false, grammarDir);

        if (paramsFile != null) {
            try {
                Params.readFile(new BufferedReader(new FileReader(paramsFile)));
            } catch (Exception e) {
                throw new CandcStartupException("could not read params file", e);
            }
        }

        Lexicon lexicon;
        try {
            lexicon = new Lexicon(lexiconFile);
        } catch (Exception e) {
            throw new CandcStartupException("error reading lexicon", e);
        }

        try {
            parser = new ChartParser(grammarDir, Params.altMarkedup,
                    Params.eisnerNormalForm, Params.MAX_WORDS, Params.MAX_SUPERCATS, Params.detailedOutput,
                    oracleFscore, Params.adaptiveSupertagging, ruleInstancesParams,
                    lexicon, featuresFile, weightsFile, Params.lambda, Params.newFeatures);
        } catch (Exception e) {
            throw new CandcStartupException("error initializing chart parser", e);
        }

        viterbiDecoder = new ViterbiDecoder();
        log = new PrintWriter(System.out, true);
    }

    public List<String> parse(String inputSentences) {
        List<String> parserOutput = new ArrayList<String>();
        try {
            log = new PrintWriter(System.out, true);

            // C&C wants an input stream, so wrap up the string in one
            BufferedReader inputReader = new BufferedReader(new StringReader(inputSentences));

            while (true) {
                ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
                PrintWriter outputWriter = new PrintWriter(new OutputStreamWriter(outputStream));

                // the 1, 1, 1 arguments are defaults for the from-toSentence args, used in printForest, but not working here
                if (!parser.parseSentence(inputReader, null, log, Params.betas, 1, 1, 1, Params.goldInput)) {
                    // parseSentence returns false if end of input file
                    break;
                }

                if (!parser.missingSupertag) {
                    // if maxWords exceeded just print new line (below)
                    if (!parser.maxWordsExceeded) {
                        if (parser.maxSuperCatsExceeded) {
                            log.println("maxSuperCats exceeded");
                        } else {
                            boolean success = parser.calcScores();

                            if (success) {
                                viterbiDecoder.decode(parser.chart, parser.sentence);
                                viterbiDecoder.print(outputWriter, parser.categories.dependencyRelations, parser.sentence);
                                parser.sentence.printC_line(outputWriter);
                            } else {
                                log.println("No root category.");
                            }
                        }
                    }
                }
                outputWriter.println();
                parserOutput.add(outputStream.toString());
            }
        } finally {
            if (log != null) {
                log.close();
            }
        }
        return parserOutput;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("C&C parser");
        argParser.description("Run the C&C parser, providing access to it via Py4J");
        argParser.addArgument("weights_file").help("Path to weights file (parsing model)");
        argParser.addArgument("grammar_dir").help("Path to grammar dir");
        argParser.addArgument("lexicon_file").help("Path to lexicon file");
        argParser.addArgument("features_file").help("Path to features file");
        argParser.addArgument("--port").type(Integer.class).help("Specify a port for gateway server to run on").setDefault(0);
        argParser.addArgument("--python-port").type(Integer.class).help("Specify a port for gateway server to use " +
                "to response to Python").setDefault(0);
        argParser.addArgument("--params").help("Path to params file. Overrides default parser params");

        Namespace opts = null;
        try {
            opts = argParser.parseArgs(args);
        } catch (ArgumentParserException e) {
            System.err.println("Error in command-line arguments: " + e);
            System.exit(1);
        }

        CandcGateway entryPoint = null;
        try {
            // Load the gateway instance
            entryPoint = new CandcGateway(
                    opts.getString("weights_file"),
                    opts.getString("params"),
                    opts.getString("grammar_dir"),
                    opts.getString("lexicon_file"),
                    opts.getString("features_file")
            );
        } catch (Exception e) {
            System.err.println("Error initializing C&C parser");
            e.printStackTrace();
            System.out.println("ERROR");
            System.exit(1);
        }
        try {
            // Create a gateway server, using this as an entry point
            Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"), "PORT ");
        } catch (Exception e) {
            System.err.println("Error starting up C&C parser gateway");
            e.printStackTrace();
            System.exit(1);
        }
    }

    public class CandcStartupException extends Exception {
        public CandcStartupException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
