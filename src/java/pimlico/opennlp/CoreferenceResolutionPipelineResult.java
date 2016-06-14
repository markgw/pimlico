package pimlico.opennlp;

import opennlp.tools.coref.DiscourseEntity;
import opennlp.tools.parser.Parse;
import opennlp.tools.util.Span;

/**
 * Data structure to contain all the output from the tools on the coreference resolution pipeline when they're
 * all executed together.
 */
public class CoreferenceResolutionPipelineResult {
    public final DiscourseEntity[] entities;
    public final Parse[] parses;
    public final String[] posTags;
    public final String[] tokenizedSentences;
    public final Span[] sentenceSpans;

    public CoreferenceResolutionPipelineResult(DiscourseEntity[] entities, Parse[] parses, String[] posTags, String[] tokenizedSentences, Span[] sentenceSpans) {
        this.entities = entities;
        this.parses = parses;
        this.posTags = posTags;
        this.tokenizedSentences = tokenizedSentences;
        this.sentenceSpans = sentenceSpans;
    }
}
