# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import csv
import os
from cStringIO import StringIO
from sklearn.manifold.mds import MDS
from sklearn.metrics.pairwise import cosine_distances

import numpy

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.plotting import PlotOutputWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        num_words = self.info.options["words"]

        # Get values and labels from the inputs
        self.log.info("Loading vectors")
        word2vec_model = self.info.get_input("vectors").load_model()
        vocab = word2vec_model.index2word
        self.log.info("Loaded vectors for {} words".format(len(vocab)))

        if len(vocab) > num_words:
            # Don't need all these vectors
            # Just take the most frequent words
            self.log.info("Limiting to {} most frequent".format(num_words))
            vocab.sort(key=lambda w: word2vec_model.vocab[w].count, reverse=True)
            vocab = vocab[:num_words]

        vecs = word2vec_model[vocab]
        # Compute cosine distances, since TSNE only offers euclidean as built-in
        sims = cosine_distances(vecs)
        # Deal with any slight negatives
        sims[numpy.where(sims < 0.)] = 0.

        # Run MDS reduction
        self.log.info("Running MDS reduction to 2D")
        mds = MDS(n_components=2, dissimilarity="precomputed")
        red_vecs = mds.fit_transform(sims)

        self.log.info("Outputting data and plotting code")
        with PlotOutputWriter(self.info.get_absolute_output_dir("plot")) as writer:
            # Prepare data to go to CSV file
            io = StringIO()
            csv_writer = csv.writer(io)
            for label, value in zip(vocab, red_vecs):
                csv_writer.writerow([unicode(label).encode("utf8"), str(float(value[0])), str(float(value[1]))])
            writer.data = io.getvalue()

            # Use a standard template plot python file
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "plot_template.py"), "r") as f:
                plotting_code = f.read()
            # Remove the first line, which is a comment to explain what the file is
            plotting_code = "\n".join(plotting_code.splitlines()[1:])
            writer.plotting_code = plotting_code

        # Written the plot code and data
        # Now do the plotting
        self.log.info("Running plotter")
        plot_output = self.info.get_output("plot")
        plot_output.plot()

        self.log.info("Plot output to %s" % plot_output.pdf_path)
        self.log.info("Customize plot by editing %s and recompiling (python ploy.py)" % plot_output.script_path)
