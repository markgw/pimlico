package pimlico.caevo;

import caevo.SieveDocument;
import caevo.util.Ling;
import caevo.util.Pair;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.ling.HasWord;
import edu.stanford.nlp.parser.lexparser.LexicalizedParser;
import edu.stanford.nlp.trees.GrammaticalStructureFactory;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class Tempeval3Parser extends caevo.Tempeval3Parser {
    public Tempeval3Parser(String[] args) {
        super(args);
    }

    /**
     * Simply provides a public version of the raw text parser.
     *
     */
    public static SieveDocument parseText(String filename, String text, LexicalizedParser parser, GrammaticalStructureFactory gsf) {
        List<List<HasWord>> sentencesNormInvertible = new ArrayList<List<HasWord>>();
        sentencesNormInvertible.addAll(Ling.getSentencesFromTextNormInvertible(text));

        if( sentencesNormInvertible.size() > 0 ) {
            String trailingWhite = trailingWhitespace(text);
            List<HasWord> sentence = sentencesNormInvertible.get(sentencesNormInvertible.size()-1);
            CoreLabel cl = (CoreLabel)sentence.get(sentence.size()-1);
            cl.set(CoreAnnotations.AfterAnnotation.class, trailingWhite);
        }

        SieveDocument sdoc = new SieveDocument((new File(filename)).getName());

        for( List<HasWord> sent : sentencesNormInvertible ) {
            Pair<String,String> parseDep = parseDep(sent, parser, gsf);
            List<CoreLabel> cls = new ArrayList<CoreLabel>();
            for( HasWord word : sent ) cls.add((CoreLabel)word);
            sdoc.addSentence(buildString(sent, 0, sent.size()), cls, parseDep.first(), parseDep.second(), null, null);
        }

        return sdoc;
    }
}
