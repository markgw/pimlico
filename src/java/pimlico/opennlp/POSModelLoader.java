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
