import random

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.features import TermFeatureListCorpus, KeyValueListCorpus
from pimlico.datatypes.tar import TarredCorpus


# Subclass TermFeatureListCorpus so that inputs expecting one can accept this
# TODO There should be a better superclass for doc-doc filters like this
class TermFeatureListCorpusFilter(TermFeatureListCorpus):
    def __init__(self, input_datatype, pipeline, **kwargs):
        TarredCorpus.__init__(self, None, pipeline, **kwargs)
        self.input_datatype = input_datatype

    def __len__(self):
        return len(self.input_datatype)

    def archive_iter(self, subsample=None, start=0):
        # TODO Implement this, which does the key
        tarballs = self.tarballs

        current_archive = 0
        current_archive_count = 0

        for file_num, (doc_name, doc) in enumerate(self.input_datatype):
            # Allow the first portion of the corpus to be skipped
            if file_num < start:
                continue
            # If subsampling, decide whether to extract this file
            if subsample is not None and random.random() > subsample:
                # Reject this file
                continue

            # Check whether we've put enough files in the current archive to move onto the next
            if current_archive_count == self.archive_size:
                current_archive += 1
                current_archive_count = 0

            yield tarballs[current_archive], doc_name, doc

    def data_ready(self):
        return self.input_datatype.data_ready()


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "term_feature_list_filter"
    module_inputs = [("key_values", KeyValueListCorpus)]
    module_outputs = [("term_features", TermFeatureListCorpusFilter)]
    module_options = [
        # TODO Add some options
    ]
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype):
        if output_name == "term_features":
            return TermFeatureListCorpusFilter(self.pipeline, self.get_input("key_values"))
        else:
            return super(ModuleInfo, self).instantiate_output_datatype(output_name, output_datatype)
