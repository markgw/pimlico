package pimlico.opennlp;

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
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Wrapper around OpenNLP's coreference resolution tool to provide access to it via Py4J for Pimlico module.
 */
public class CoreferenceResolverGateway {
    private Linker corefLinker;

    public CoreferenceResolverGateway(File modelsDir) throws ModelLoadError {
        // Load a coref model
        try {
            //corefLinker = new DefaultLinker(modelsDir.getAbsolutePath(), LinkerMode.TEST);
            corefLinker = new TreebankLinker(modelsDir.getAbsolutePath(), LinkerMode.TEST);
        } catch (IOException e) {
            throw new ModelLoadError("could not load coref model: " + e.getMessage());
        }
    }

    /**
     * Like resolveCoreference(), but accepts PTB-style parse trees for each sentence, which will be
     * read into OpenNLP Parse objects, before handing over to resolveCoreference().
     *
     * @param sentences PTB-style parse trees as strings
     * @return output of coref
     */
    public DiscourseEntity[] resolveCoreferenceFromTrees(List<String> sentences) {
        List<Parse> parses = new ArrayList<Parse>();
        for (String sentence : sentences)
            parses.add(Parse.parseParse(sentence));
        return resolveCoreference(parses);
    }

    public DiscourseEntity[] resolveCoreference(List<Parse> sentences) {
        List<Mention> mentions = new ArrayList<Mention>();

        // Collect mentions from each sentence
        int sentenceNum = 0;
        for (Parse parsedSentence : sentences) {
            // Get mentions from this sentence
            mentions.addAll(Arrays.asList(getMentions(parsedSentence, sentenceNum)));
            sentenceNum++;
        }

        Mention[] mentionArray = mentions.toArray(new Mention[mentions.size()]);
        try {
            // Run coreference resolution
            return corefLinker.getEntities(mentionArray);
        } catch (RuntimeException e) {
            // Sadly this happens occasionally: handle it nicely
            System.out.println("Runtime exception getting entities: ");
            e.printStackTrace();
            return new DiscourseEntity[0];
        }
    }

    private Mention[] getMentions(Parse parse, int sentenceNum) {
        // If there was an error reading parse data, we might have no parse: give no mentions
        if (parse == null)
            return new Mention[0];

        // Wrap up the parse
        opennlp.tools.coref.mention.Parse mentionParse = new DefaultParse(parse, sentenceNum);
        // Extract mentions
        Mention[] mentions = corefLinker.getMentionFinder().getMentions(mentionParse);

        // This is taken from CoreferencerTool...
        //construct new parses for mentions which don't have constituents.
        for (Mention mention : mentions) {
            if (mention.getParse() == null) {
                //not sure how to get head index, but its not used at this point.
                Parse snp = new Parse(parse.getText(), mention.getSpan(), "NML", 1.0, 0);
                parse.insert(snp);
                mention.setParse(new DefaultParse(snp, sentenceNum));
            }
        }

        return mentions;
    }

    public static class ModelLoadError extends Exception {
        public ModelLoadError(String message) {
            super(message);
        }
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Coreference");
        argParser.description("Run the OpenNLP coreference resolver, providing access to it via Py4J");
        argParser.addArgument("coref_model_dir").help("Path to coref model dir");
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

        String corefModelDir = opts.getString("coref_model_dir");

        // Load the gateway instance
        CoreferenceResolverGateway entryPoint = null;
        try {
            entryPoint = new CoreferenceResolverGateway(new File(corefModelDir));
        } catch (ModelLoadError modelLoadError) {
            modelLoadError.printStackTrace();
            System.exit(1);
        }
        // Create a gateway server, using this as an entry point
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
