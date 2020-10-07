// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

package pimlico.opennlp;

import opennlp.tools.sentdetect.SentenceModel;

import java.io.IOException;
import java.io.InputStream;

/**
 * Loads a Tokenizer Model.
 */
final class SentenceModelLoader extends QuietModelLoader<SentenceModel> {
    public SentenceModelLoader() {
        super("Sentence Detector");
    }

    @Override
    protected SentenceModel loadModel(InputStream modelIn) throws IOException {
        return new SentenceModel(modelIn);
    }
}
