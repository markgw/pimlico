// This file is part of Pimlico
// Copyright (C) 2016 Mark Granroth-Wilding
// Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

package pimlico.opennlp;

import opennlp.tools.cmdline.CmdLineUtil;
import opennlp.tools.cmdline.TerminateToolException;
import opennlp.tools.util.InvalidFormatException;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;

/**
 * Like OpenNLP's model loader, but doesn't output stuff needlessly to stderr.
 */
public abstract class QuietModelLoader<T> {
    private final String modelName;

    protected QuietModelLoader(String modelName) {
        if (modelName == null)
            throw new IllegalArgumentException("modelName must not be null!");
        this.modelName = modelName;
    }

    protected abstract T loadModel(InputStream modelIn) throws IOException;

    public T load(File modelFile) {
        CmdLineUtil.checkInputFile(modelName + " model", modelFile);
        InputStream modelIn = new BufferedInputStream(CmdLineUtil.openInFile(modelFile));

        T model;
        try {
            model = loadModel(modelIn);
        } catch (InvalidFormatException e) {
            System.err.println("failed");
            throw new TerminateToolException(-1, "Model has invalid format", e);
        } catch (IOException e) {
            System.err.println("failed");
            throw new TerminateToolException(-1, "IO error while loading model file '" + modelFile + "'", e);
        } finally {
            // will not be null because openInFile would
            // terminate in this case
            try {
                modelIn.close();
            } catch (IOException e) {
                // sorry that this can fail
            }
        }
        return model;
    }
}
