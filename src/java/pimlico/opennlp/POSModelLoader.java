// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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
