package pimlico.opennlp;

import com.google.common.base.Joiner;
import opennlp.tools.cmdline.parser.ParserTool;
import opennlp.tools.coref.*;
import opennlp.tools.coref.mention.DefaultParse;
import opennlp.tools.coref.mention.Mention;
import opennlp.tools.parser.Parse;
import opennlp.tools.parser.Parser;
import opennlp.tools.parser.ParserFactory;
import opennlp.tools.parser.ParserModel;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Created by mtw29 on 23/04/14.
 */
public class CoreferenceResolver {
    private Parser parser;
    private Linker corefLinker;

    public CoreferenceResolver(File parsingModel, File modelsDir) throws ModelLoadError {
        InputStream modelIn = null;
        try {
            // Load the parsing model
            modelIn = new FileInputStream(parsingModel);
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

        // Load a coref model
        try {
            //corefLinker = new DefaultLinker(modelsDir.getAbsolutePath(), LinkerMode.TEST);
            corefLinker = new TreebankLinker(modelsDir.getAbsolutePath(), LinkerMode.TEST);
        } catch (IOException e) {
            throw new ModelLoadError("could not load coref model: " + e.getMessage());
        }
    }

    public DiscourseEntity[] resolveCoreferenceParsed(List<ParsedSentence> sentences) {
        List<Mention> mentions = new ArrayList<Mention>();

        // Collect mentions from each sentence
        int sentenceNum = 0;
        for (ParsedSentence sentence : sentences) {
            // Get mentions from this sentence
            mentions.addAll(Arrays.asList(getMentions(sentence.parse, sentenceNum)));
            sentenceNum++;
        }

        Mention[] mentionArray = mentions.toArray(new Mention[mentions.size()]);
        try {
            // Run coreference resolution
            return corefLinker.getEntities(mentionArray);
        } catch (RuntimeException e) {
            // Sadly this happens occasionally: handle it nicely
            return new DiscourseEntity[0];
        }
    }

    public Parse parse(String[] words) {
        // Run the parser to get max 1 parse
        Parse[] parses = ParserTool.parseLine(Joiner.on(' ').join(words), parser, 1);
        // Return the parse if we got one
        if (parses.length > 0) {
            return parses[0];
        } else {
            return null;
        }
    }

    public Mention[] getMentions(String[] words, int sentenceNum) {
        // Run the parser on the sentence
        Parse parse = parse(words);
        return getMentions(parse, sentenceNum);
    }

    public Mention[] getMentions(Parse parse, int sentenceNum) {
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

    public DiscourseEntity[] resolveCoreference(List<String[]> sentences) {
        List<Mention> mentions = new ArrayList<Mention>();

        // Collect mentions from each sentence
        int sentenceNum = 0;
        for (String[] sentence : sentences) {
            // Get mentions from this sentence
            mentions.addAll(Arrays.asList(getMentions(sentence, sentenceNum)));
            sentenceNum++;
        }

        Mention[] mentionArray = mentions.toArray(new Mention[mentions.size()]);
        // Run coreference resolution
        return corefLinker.getEntities(mentionArray);
    }

    public static class ModelLoadError extends Exception {
        public ModelLoadError(String message) {
            super(message);
        }
    }
}
