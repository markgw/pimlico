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
import org.maltparser.concurrent.ConcurrentMaltParserModel;
import org.maltparser.concurrent.ConcurrentMaltParserService;
import pimlico.core.Py4JGatewayStarter;

import java.io.*;
import java.net.URL;

/**
 * Wrapper around the new Java C&C to provide access to it via Py4J for Pimlico module.
 * Based on Parser class.
 */
public class CandcGateway {
    PrintWriter log;
    ChartParser parser;
    ViterbiDecoder viterbiDecoder;

    public CandcGateway(String weightsFile, String paramsFile, String grammarDir, String lexiconFile, String featuresFile) {
        /*
         * parameters where the defaults (set for the beam parser) need changing for the Viterbi parser
         */
        Params.MAX_SUPERCATS = 1000000;
        Params.newFeatures = false;
        Params.betas[0] = 0.075;
        Params.betas[1] = 0.03;
        Params.betas[2] = 0.01;
        Params.betas[3] = 0.001;
        /*
         * Params.adaptiveSupertagging = false;
         * Params.betas = { 0.0001, 0.001, 0.01, 0.03, 0.075 };
         * true indicates beta values get larger, and first value is betas[0];
         * false is the opposite, and first value is betas[2]
         */

        boolean oracleFscore = false;
        boolean seenRules = true;
        RuleInstancesParams ruleInstancesParams = new RuleInstancesParams(seenRules, false, false, false, false, false, grammarDir);

        if (paramsFile != null) {
            BufferedReader paramsIn = null;
            try {
                paramsIn = new BufferedReader(new FileReader(paramsFile));
                Params.readFile(paramsIn);
            } catch (IOException e) {
                System.err.println(e);
                return;
            }
        }

        Params.printValues();
        System.out.println("seen rules: " + seenRules + "\n****************\n");

        Lexicon lexicon = null;

        try {
            lexicon = new Lexicon(lexiconFile);
        } catch (IOException e) {
            System.err.println(e);
            return;
        }

        parser = null;
        try {
            System.out.println("reading in features and weights file");

            parser = new ChartParser(grammarDir, Params.altMarkedup,
                    Params.eisnerNormalForm, Params.MAX_WORDS, Params.MAX_SUPERCATS, Params.detailedOutput,
                    oracleFscore, Params.adaptiveSupertagging, ruleInstancesParams,
                    lexicon, featuresFile, weightsFile, Params.lambda, Params.newFeatures);
        } catch (IOException e) {
            System.err.println(e);
            return;
        }

        viterbiDecoder = new ViterbiDecoder();
        log = new PrintWriter(System.out, true);
    }

    public String parse(String inputSentence) {
        try {
            log = new PrintWriter(System.out, true);

            // C&C wants an input stream, so wrap up the string in one
            BufferedReader inputReader = new BufferedReader(new InputStreamReader(
                    new ByteArrayInputStream(inputSentence.getBytes())));
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            PrintWriter outputWriter = new PrintWriter(new OutputStreamWriter(outputStream));

            /*
             * the 1, 1, 1 arguments are defaults for the from - toSentence args, used in printForest, but not
             * working here
             * parseSentence returns false if end of input file
             */

            if (!parser.parseSentence(inputReader, null, log, Params.betas, 1, 1, 1, Params.goldInput)) {
                log.println("No such sentence; no more sentences.");
                return "";
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
            return outputStream.toString();
        } finally {
            if (log != null) {
                log.close();
            }
        }
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
            CandcGateway entryPoint = new CandcGateway(model);
            // Create a gateway server, using this as an entry point
            Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
        } catch (Exception e) {
            System.err.println("Error starting up Malt parser gateway");
            e.printStackTrace();
            System.exit(1);
        }
    }
}
