// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

package pimlico.opennlp;

import com.google.common.base.Joiner;
import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;
import opennlp.tools.namefind.NameFinderME;
import opennlp.tools.namefind.TokenNameFinderModel;
import opennlp.tools.util.Span;
import pimlico.core.Py4JGatewayStarter;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Py4J gateway to POS tagger.
 */
public class NERGateway {
    NameFinderME tagger;
    private Joiner whitespaceJoiner;

    public NERGateway(File modelFile) {
        // Load model
        TokenNameFinderModel model = new NameFinderModelLoader().load(modelFile);
        tagger = new NameFinderME(model);
        whitespaceJoiner = Joiner.on(' ');
    }

    /**
     * NER tag an array of sentences. Assumed to be tokenized already, so that they can be split on
     * spaces.
     *
     * @param sentences input sentences
     * @return array of POS tagged sentences

    public String[] nerTag(List sentences) {
        String[] result = new String[sentences.size()];
        List<Span[]> spans = nerFind(sentences);
        String[] words;
        Span[] sentenceSpans;

        for (int i=0; i < spans.size(); i++) {
            words = ((String) sentences.get(i)).split(" ");
            sentenceSpans = spans.get(i);
            // Pre-fill tags with Os
            String[] tags = new String[words.length];
            for (int j=0; j < tags.length; j++)
                tags[j] = "O";

            // Fill in tags for each span
            for (Span span : sentenceSpans) {
                // Deal with nested spans by accepting the longest
                // If the start and end of the span are covered by one already processed, skip it
                if (!tags[span.getStart()].equals("O") && !tags[span.getEnd()].equals("O"))
                    continue;

                // Otherwise fill in the whole span with tags
                if (span.length() == 1)
                    // Length 1 span: use special start and end tag
                    tags[span.getStart()] = "BNE_ENE";
                else if (span.length() > 0) {
                    // Set special tags for start and end
                    tags[span.getStart()] = "BNE";
                    tags[span.getEnd()-1] = "ENE";
                    // Fill in everything in between with "in" tag
                    for (int j=span.getStart()+1; j < span.getEnd()-1; j++)
                        tags[j] = "INE";
                }
            }

            result[i] = whitespaceJoiner.join(tags);
        }
        return result;
    }*/

    public List<Span[]> nerFind(List sentences) {
        ArrayList<Span[]> result = new ArrayList<Span[]>();
        String[] words;

        for (Object sentence : sentences) {
            words = ((String) sentence).split(" ");
            result.add(tagger.find(words));
        }
        // Reset the name finder ready for the next document
        tagger.clearAdaptiveData();
        return result;
    }

    public static void main(String[] args) {
        ArgumentParser argParser = ArgumentParsers.newArgumentParser("NER tag");
        argParser.description("Run the OpenNLP named entity tagger, providing access to it via Py4J");
        argParser.addArgument("model").help("NER tagger model");
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
        NERGateway entryPoint = new NERGateway(new File(opts.getString("model")));
        // Run the gateway
        Py4JGatewayStarter.startGateway(entryPoint, opts.getInt("port"), opts.getInt("python_port"));
    }
}
