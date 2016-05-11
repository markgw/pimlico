// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.opennlp;

import opennlp.tools.tokenize.TokenizerModel;

import java.io.IOException;
import java.io.InputStream;

/**
 * Loads a Tokenizer Model quietly.
 */
public final class TokenizerModelLoader extends QuietModelLoader<TokenizerModel> {
    public TokenizerModelLoader() {
        super("Tokenizer");
    }

    @Override
    protected TokenizerModel loadModel(InputStream modelIn) throws IOException {
        return new TokenizerModel(modelIn);
    }
}
