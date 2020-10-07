// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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
