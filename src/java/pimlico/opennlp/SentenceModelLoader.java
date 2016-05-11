// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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
