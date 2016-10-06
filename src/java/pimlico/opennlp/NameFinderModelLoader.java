// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.opennlp;

import opennlp.tools.namefind.TokenNameFinderModel;

import java.io.IOException;
import java.io.InputStream;

/**
 * Loads an NER Model quietly.
 */
public final class NameFinderModelLoader extends QuietModelLoader<TokenNameFinderModel> {
    public NameFinderModelLoader() {
        super("ner-tagger");
    }

    @Override
    protected TokenNameFinderModel loadModel(InputStream modelIn) throws IOException {
        return new TokenNameFinderModel(modelIn);
    }
}
