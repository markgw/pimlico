import numpy as np

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # Load the model
        model = self.info.get_input("model").load_model()
        opts = self.info.options
        num_words = opts["num_words"]

        self.log.info("Loaded LDA model with {} topics".format(model.num_topics))

        # Get the per-topic word distribution from the LDA model
        topic_word_probs = model.state.get_lambda()
        # Get the IDs of the top words
        top_word_ids = np.argsort(-topic_word_probs, axis=-1)[:, :num_words]
        # Look up the actual words
        topics_top_words = [
            [model.id2word[i] for i in topic_words] for topic_words in top_word_ids
        ]

        with self.info.get_output_writer("top_words") as writer:
            writer.write_topics_words(topics_top_words)
