package pimlico.malt;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.coref.DiscourseEntity;
import opennlp.tools.coref.Linker;
import opennlp.tools.coref.LinkerMode;
import opennlp.tools.coref.TreebankLinker;
import opennlp.tools.coref.mention.DefaultParse;
import opennlp.tools.coref.mention.Mention;
import opennlp.tools.parser.Parse;
import org.maltparser.concurrent.ConcurrentMaltParserModel;
import org.maltparser.concurrent.ConcurrentMaltParserService;
import org.maltparser.core.exception.MaltChainedException;
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.io.IOException;
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
    public String[] parseFromCoNLL(String[] conllSentence) throws MaltChainedException {
        // Parse the sentence
        return model.parseTokens(conllSentence);
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
