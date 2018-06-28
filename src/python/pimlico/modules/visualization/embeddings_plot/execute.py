# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import csv
import os
from cStringIO import StringIO
from itertools import dropwhile
from sklearn.manifold.mds import MDS
from sklearn.manifold.t_sne import TSNE
from sklearn.metrics.pairwise import cosine_distances, euclidean_distances, manhattan_distances

import numpy

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.old_datatypes.plotting import PlotOutputWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        num_words = self.info.options["words"]
        skip_words = self.info.options["skip"]
        cmap = self.info.options["cmap"]
        colour_list = self.info.options["colors"]
        metric = self.info.options["metric"]

        reduction = self.info.options["reduction"]
        reduction_name = {"mds": "MDS", "tsne": "t-SNE"}[reduction]

        # Get values and labels from the inputs
        self.log.info("Loading vectors")
        lang_embeddings = self.info.get_input("vectors", always_list=True)
        vocab = []
        vecs = []
        source_ids = []
        for e_num, e in enumerate(lang_embeddings):
            lvocab = e.index2word
            self.log.info("Loaded vectors for {} words".format(len(lvocab)))

            # Just take the most frequent words
            self.log.info("Limiting to {} most frequent words, skipping {}".format(num_words, skip_words))
            lvocab.sort(key=lambda w: e.vocab[w].count, reverse=True)
            lvocab = lvocab[skip_words:num_words+skip_words]
            vocab.extend(lvocab)
            source_ids.extend([e_num]*len(lvocab))

            vecs.append(e[lvocab])
        vecs = numpy.vstack(tuple(vecs))

        # Compute cosine distances, since TSNE only offers euclidean as built-in
        if metric == "euclidean":
            distances = euclidean_distances(vecs)
        elif metric == "manhattan":
            distances = manhattan_distances(vecs)
        else:
            distances = cosine_distances(vecs)
        # Deal with any slight negatives
        distances[numpy.where(distances < 0.)] = 0.

        # Run MDS/t-SNE reduction
        self.log.info("Running {} reduction to 2D".format(reduction_name))
        if reduction == "tsne":
            red = TSNE(n_components=2, metric="precomputed")
        else:
            red = MDS(n_components=2, dissimilarity="precomputed")
        red_vecs = red.fit_transform(distances)

        if cmap is not None:
            # A colour map has been supplied: process the labels to apply colouring
            def word2col(s):
                for prefix, cname in cmap.items():
                    if s.startswith(prefix):
                        return s[len(prefix):], cname
                return s, "b"
            vocab, colours = zip(*map(word2col, vocab))
        elif colour_list is not None:
            colours = [colour_list[i] for i in source_ids]
        else:
            colours = ["b" for __ in vocab]

        title = "{} reduction, {} distances".format(reduction_name, metric)

        self.log.info("Outputting data and plotting code")
        with PlotOutputWriter(self.info.get_absolute_output_dir("plot")) as writer:
            # Prepare data to go to CSV file
            io = StringIO()
            csv_writer = csv.writer(io)
            for label, value, c in zip(vocab, red_vecs, colours):
                csv_writer.writerow([unicode(label).encode("utf8"), str(float(value[0])), str(float(value[1])), c])
            writer.data = io.getvalue()

            # Use a standard template plot python file
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "plot_template.py"), "r") as f:
                plotting_code = f.read()
            # Remove any comments at the beginning, which explain what the file is
            plotting_code = "\n".join(dropwhile(lambda l: len(l) == 0 or l.startswith("#"), plotting_code.splitlines()))
            writer.plotting_code = plotting_code.replace("<TITLE>", title)

        # Written the plot code and data
        # Now do the plotting
        self.log.info("Running plotter")
        plot_output = self.info.get_output("plot")
        plot_output.plot()

        self.log.info("Plot output to %s" % plot_output.pdf_path)
        self.log.info("Customize plot by editing %s and recompiling (python plot.py)" % plot_output.script_path)
