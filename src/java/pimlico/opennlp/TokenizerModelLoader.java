// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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
