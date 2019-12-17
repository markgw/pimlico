import logging
from logging import getLogger

from gensim.models import LdaModel, TfidfModel

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.gensim.utils import GensimCorpus
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # Load corpus from input
        corpus = self.info.get_input("corpus")
        vocab = self.info.get_input("vocab").get_data()
        # Get the Gensim data structure for the vocab as well
        #gen_dict = vocab.as_gensim_dictionary()

        opts = self.info.options

        # Prepare IDs for special terms to ignore
        ignore_terms = opts["ignore_terms"]
        if ignore_terms:
            self.log.info("Ignoring terms: {}".format(
                ", ".join("'{}'".format(t) for t in ignore_terms)
            ).encode("utf-8"))
        ignore_ids = [vocab.token2id[term] for term in ignore_terms]

        # Set up logging, so that we see Gensim's progress as it trains
        lda_logger = getLogger('gensim.models.ldamodel')
        hnd = logging.StreamHandler()
        hnd.setLevel(logging.INFO)
        fmt = logging.Formatter('%(asctime)s - Gensim - %(levelname)s - %(message)s')
        hnd.setFormatter(fmt)
        lda_logger.addHandler(hnd)
        lda_logger.setLevel(logging.INFO)

        # Wrap the corpus to present it as bags of words to Gensim
        gensim_corpus = GensimCorpus(corpus, ignore_ids=ignore_ids)

        if opts["tfidf"]:
            # We can also use the dictionary directly to compute the tfidf stats, but then we need
            # to be sure that the frequencies stored there reflect this corpus
            # Perhaps in future add an option to use these stats, as it's quite a lot quicker
            self.log.info("Preparing tf-idf transformation")
            pbar = get_progress_bar(len(gensim_corpus), title="Counting")
            gensim_corpus = TfidfModel(pbar(gensim_corpus), id2word=vocab.id2token)[gensim_corpus]

        # Train gensim model
        self.log.info("Training Gensim model with {} topics on {} documents".format(opts["num_topics"], len(corpus)))

        if opts["multicore"]:
            from gensim.models.ldamulticore import LdaMulticore
            num_workers = self.info.pipeline.processes
            self.log.info("Using multicore LDA implementation with {} workers".format(num_workers))

            # Set all parameters from options
            lda = LdaMulticore(
                gensim_corpus, workers=num_workers,
                num_topics=opts["num_topics"], id2word=vocab.id2token,
                chunksize=opts["chunksize"], passes=opts["passes"],
                alpha=opts["alpha"], eta=opts["eta"],
                decay=opts["decay"], offset=opts["offset"], eval_every=opts["eval_every"],
                iterations=opts["iterations"], gamma_threshold=opts["gamma_threshold"],
                minimum_probability=opts["minimum_probability"], minimum_phi_value=opts["minimum_phi_value"]
            )
        else:
            # Set all parameters from options
            lda = LdaModel(
                gensim_corpus,
                num_topics=opts["num_topics"], id2word=vocab.id2token,
                distributed=opts["distributed"], chunksize=opts["chunksize"], passes=opts["passes"],
                update_every=opts["update_every"], alpha=opts["alpha"], eta=opts["eta"],
                decay=opts["decay"], offset=opts["offset"], eval_every=opts["eval_every"],
                iterations=opts["iterations"], gamma_threshold=opts["gamma_threshold"],
                minimum_probability=opts["minimum_probability"], minimum_phi_value=opts["minimum_phi_value"]
            )

        self.log.info("Training complete. Some of the learned topics:")
        for topic, topic_repr in lda.show_topics(10, 6):
            self.log.info(u"#{}: {}".format(topic, topic_repr))

        self.log.info("Storing model")
        with self.info.get_output_writer("model") as w:
            w.write_model(lda)
