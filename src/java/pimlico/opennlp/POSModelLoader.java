// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

package pimlico.opennlp;

import opennlp.tools.postag.POSModel;

import java.io.IOException;
import java.io.InputStream;

/**
 * Loads a POS Model quietly.
 */
public final class POSModelLoader extends QuietModelLoader<POSModel> {
    public POSModelLoader() {
        super("pos-tagger");
    }

    @Override
    protected POSModel loadModel(InputStream modelIn) throws IOException {
        return new POSModel(modelIn);
    }
}
