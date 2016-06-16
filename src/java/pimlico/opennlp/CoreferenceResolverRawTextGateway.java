package pimlico.opennlp;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.coref.DiscourseEntity;
import opennlp.tools.parser.Parse;
import opennlp.tools.util.Span;
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.util.Arrays;
import java.util.List;

/**
 * Performs end-to-end coreference resolution on raw text.
 *
 * Combines the functionality of the sentence splitter, tokenizer, pos tagger, parser and coreference resolver
 * and returns the results from all of them.
 */
public class CoreferenceResolverRawTextGateway {
    private final TokenizerGateway tokenizerGateway;
    private final PosTaggerGateway posTaggerGateway;
    private final ParserGateway parserGateway;
    private final CoreferenceResolverGateway coreferenceResolverGateway;

    public CoreferenceResolverRawTextGateway(
            File sentModelFile, File tokModelFile, File posModelFile, File parserModelFile,
            File corefModelDir, Integer timeout)
            throws CoreferenceResolverGateway.ModelLoadError, ParserGateway.ModelLoadError {
        tokenizerGateway = new TokenizerGateway(sentModelFile, tokModelFile);
        posTaggerGateway = new PosTaggerGateway(posModelFile);
        parserGateway = new ParserGateway(parserModelFile);
        coreferenceResolverGateway = new CoreferenceResolverGateway(corefModelDir, timeout);
    }

    public CoreferenceResolutionPipelineResult resolveCoreference(String inputText) {
        DiscourseEntity[] entities = null;
        Parse[] parses = null;
        String[] posTags = null;

        // Do sentence splitting separately, so we get the spans
        Span[] sentenceSpans = tokenizerGateway.sentenceSplitSpans(inputText);
        // This actually repeats the sentence splitting, but it doesn't take long, so no matter
        String[] tokenizedSentences = tokenizerGateway.tokenize(inputText);
        if (tokenizedSentences != null) {
            posTags = posTaggerGateway.posTag(Arrays.asList(tokenizedSentences));
            List<Parse> parseTrees = parserGateway.parse(Arrays.asList(tokenizedSentences));
            if (parseTrees != null) {
                parses = parseTrees.toArray(new Parse[parseTrees.size()]);
                entities = coreferenceResolverGateway.resolveCoreference(parseTrees);
            }
        }
        return new CoreferenceResolutionPipelineResult(entities, parses, posTags, tokenizedSentences, sentenceSpans);
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("CoreferenceRawText");
        argParser.description("Run the OpenNLP coreference resolver pipeline on raw text, providing access to it via Py4J");
        argParser.addArgument("sent_model_file").help("Path to sentence splitting model file");
        argParser.addArgument("token_model_file").help("Path to sentence tokenization model file");
        argParser.addArgument("pos_model_file").help("Path to sentence pos tagger model file");
        argParser.addArgument("parser_model_file").help("Path to sentence parser model file");
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

        File sentModelFile = new File(opts.getString("sent_model_file"));
        File tokenModelFile = new File(opts.getString("token_model_file"));
        File posModelFile = new File(opts.getString("pos_model_file"));
        File parserModelFile = new File(opts.getString("parser_model_file"));
        File corefModelDir = new File(opts.getString("coref_model_dir"));

        // Load the gateway instance
        CoreferenceResolverRawTextGateway entryPoint = null;
        try {
            entryPoint = new CoreferenceResolverRawTextGateway(
                    sentModelFile, tokenModelFile, posModelFile, parserModelFile, corefModelDir, opts.getInt("timeout")
            );
        } catch (CoreferenceResolverGateway.ModelLoadError modelLoadError) {
            modelLoadError.printStackTrace();
            System.exit(1);
        } catch (ParserGateway.ModelLoadError modelLoadError) {
            modelLoadError.printStackTrace();
            System.exit(1);
        }
        // Create a gateway server, using this as an entry point
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
