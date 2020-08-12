from gensim.models import LdaSeqModel, TfidfModel

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.gensim.utils import GensimCorpus
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # Load corpus from input
        corpus = self.info.get_input("corpus")
        labels = self.info.get_input("labels")
        vocab = self.info.get_input("vocab").get_data()
        opts = self.info.options

        # Count up the labels to get the number of documents in each time slice
        slice_sizes, slice_labels = zip(*labels_to_slice_sizes(labels))

        # Prepare IDs for special terms to ignore
        ignore_terms = opts["ignore_terms"]
        if ignore_terms:
            self.log.info("Ignoring terms: {}".format(
                ", ".join("'{}'".format(t) for t in ignore_terms)
            ).encode("utf-8"))
        ignore_ids = [vocab.token2id[term] for term in ignore_terms]

        # Wrap the corpus to present it as bags of words to Gensim
        gensim_corpus = GensimCorpus(corpus, ignore_ids=ignore_ids)

        if opts["tfidf"]:
            # We can also use the dictionary directly to compute the tfidf stats, but then we need
            # to be sure that the frequencies stored there reflect this corpus
            # Perhaps in future add an option to use these stats, as it's quite a lot quicker
            self.log.info("Preparing tf-idf transformation")
            pbar = get_progress_bar(len(gensim_corpus), title="Counting")
            gensim_corpus = TfidfModel(pbar(gensim_corpus), id2word=vocab.id2token)[gensim_corpus]

        # Train gensim DTM model
        self.log.info("Training Gensim DTM with {} topics on {} time slices with {} documents in total".format(
            opts["num_topics"], len(slice_sizes), len(corpus)))
        # Set all parameters from options
        ldaseq = LdaSeqModel(
            corpus=gensim_corpus,
            num_topics=opts["num_topics"],
            time_slice=slice_sizes,
            id2word=vocab.id2token,
            chain_variance=opts["chain_variance"],
            alphas=opts["alphas"],
            em_min_iter=opts["em_min_iter"], em_max_iter=opts["em_max_iter"],
            passes=opts["passes"],
            lda_inference_max_iter=opts["lda_inference_max_iter"]
        )
        self.log.info("Training complete")

        self.log.info("Storing model")
        with self.info.get_output_writer("model") as w:
            w.write_model(ldaseq)
            w.write_labels(slice_labels)


def labels_to_slice_sizes(label_corpus):
    label_iter = iter(label_corpus)

    current_label = next(label_iter)[1].label
    current_slice_size = 1

    for doc_name, doc in label_iter:
        if doc.label != current_label:
            # Starting a new label, start a new slice
            yield current_slice_size, current_label
            current_slice_size = 1
            current_label = doc.label
        else:
            current_slice_size += 1

    yield current_slice_size, current_label
