// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

package pimlico.opennlp;

import opennlp.tools.coref.DiscourseEntity;
import opennlp.tools.parser.Parse;
import opennlp.tools.util.Span;

import java.util.ArrayList;
import java.util.List;

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

    public String[] getParseTrees() {
        List<String> results = new ArrayList<String>();
        for (Parse parse : parses) {
            // Format the parser output as a PTB tree
            StringBuffer sb = new StringBuffer();
            parse.show(sb);
            results.add(sb.toString());
        }
        return results.toArray(new String[results.size()]);
    }
}
