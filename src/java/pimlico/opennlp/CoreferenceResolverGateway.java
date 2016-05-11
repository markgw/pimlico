// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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
import java.util.concurrent.*;

/**
 * Wrapper around OpenNLP's coreference resolution tool to provide access to it via Py4J for Pimlico module.
 */
public class CoreferenceResolverGateway {
    private Linker corefLinker;
    private Integer timeout;

    public CoreferenceResolverGateway(File modelsDir, Integer timeout) throws ModelLoadError {
        // Load a coref model
        try {
            //corefLinker = new DefaultLinker(modelsDir.getAbsolutePath(), LinkerMode.TEST);
            corefLinker = new TreebankLinker(modelsDir.getAbsolutePath(), LinkerMode.TEST);
        } catch (IOException e) {
            throw new ModelLoadError("could not load coref model: " + e.getMessage());
        }
        this.timeout = timeout;
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
        return resolveCoreferenceWithTimeout(parses);
    }

    public DiscourseEntity[] resolveCoreferenceFromTreesStrings(String sentences) {
        List<Parse> parses = new ArrayList<Parse>();
        for (String sentence : sentences.split("\n\n"))
            parses.add(Parse.parseParse(sentence));
        return resolveCoreferenceWithTimeout(parses);
    }

    public DiscourseEntity[] resolveCoreferenceWithTimeout(List<Parse> sentences) {
        if (timeout == null) {
            return resolveCoreference(sentences);
        } else {
            CorefThread runner = new CorefThread(this, sentences);

            // Start up an executor service, which allows us to put a timeout on the execution
            ExecutorService executor = Executors.newSingleThreadExecutor();
            Future future = executor.submit(runner);
            // This does not cancel the already-scheduled task.
            executor.shutdown();

            try {
                future.get(timeout, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                System.out.println("Coref interrupted");
                e.printStackTrace();
                return null;
            } catch (TimeoutException e) {
                // Execution timed out, so no results to give
                System.out.println("Execution timed out after " + timeout + " secs");
                return null;
            } catch (ExecutionException e) {
                // Some other problem during execution
                System.out.println("Error running coref");
                e.printStackTrace();
                return null;
            } finally {
                // If the executor's still going (i.e. get timed out), stop it
                if (!executor.isTerminated())
                    executor.shutdownNow();
            }
            return runner.result;
        }
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
            return null;
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

    private static class CorefThread extends Thread {
        private final CoreferenceResolverGateway gateway;
        private final List<Parse> sentences;
        private DiscourseEntity[] result;

        public CorefThread(CoreferenceResolverGateway gateway, List<Parse> sentences) {
            this.gateway = gateway;
            this.sentences = sentences;
        }

        public void run() {
            result = gateway.resolveCoreference(sentences);
        }
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("Coreference");
        argParser.description("Run the OpenNLP coreference resolver, providing access to it via Py4J");
        argParser.addArgument("coref_model_dir").help("Path to coref model dir");
        argParser.addArgument("--port").type(Integer.class).help("Specify a port for gateway server to run on").setDefault(0);
        argParser.addArgument("--python-port").type(Integer.class).help("Specify a port for gateway server to use " +
                "to response to Python").setDefault(0);
        argParser.addArgument("--timeout").type(Integer.class).help("Timeout in seconds for each individual " +
                "coreference resolution task. If the timeout is exceeded, a null result is returned");

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
            entryPoint = new CoreferenceResolverGateway(new File(corefModelDir), opts.getInt("timeout"));
        } catch (ModelLoadError modelLoadError) {
            modelLoadError.printStackTrace();
            System.exit(1);
        }
        // Create a gateway server, using this as an entry point
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
