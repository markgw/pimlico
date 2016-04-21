from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.features import IndexedTermFeatureListCorpusWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_data = self.info.get_input("data")
        self.log.info("Loading dictionaries")
        term_vocab = self.info.get_input("term_vocab").get_data()
        feature_vocab = self.info.get_input("feature_vocab").get_data()

        pbar = get_progress_bar(len(input_data), title="Mapping")

        # Prepare a writer for the output data
        with IndexedTermFeatureListCorpusWriter(self.info.get_absolute_output_dir("data"), term_vocab, feature_vocab) as writer:
            # Input is given for every document in a corpus
            writer.add_data_points(
                # Doc data consists of (term, feature count dict) pairs which we can pass straight to writer
                (term, fcs)
                for doc_name, document_data in pbar(input_data) if not isinstance(document_data, InvalidDocument)
                for (term, fcs) in document_data
            )
        self.log.info("Mapper produced dataset with %d data points" % writer.metadata["length"])
