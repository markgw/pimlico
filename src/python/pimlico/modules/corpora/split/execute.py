import random

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import StringListWriter
from pimlico.datatypes.tar import TarredCorpusWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("corpus")
        input_corpus.raw_data = True

        set1_list = []
        set2_list = []
        output_set2_list = "doc_list2" in self.info.output_names
        # Track how many more docs are yet to be output to each set
        set1_remaining = len(input_corpus) * self.info.options["set1_size"]
        set2_remaining = len(input_corpus) - set1_remaining

        pbar = get_progress_bar(len(input_corpus), title="Splitting")

        # Use a generic TarredCorpusWriter, since we're just passing through the encoded data from the input
        with TarredCorpusWriter(self.info.get_absolute_output_dir("set1"),
                                gzip=input_corpus.gzip, encoding=input_corpus.encoding) as set1_writer:
            with TarredCorpusWriter(self.info.get_absolute_output_dir("set2"),
                                    gzip=input_corpus.gzip, encoding=input_corpus.encoding) as set2_writer:
                for archive_name, doc_name, doc_data in pbar(input_corpus.archive_iter()):
                    if set1_remaining == 0:
                        # Must be set 2
                        put_in, lst = set2_writer, set2_list
                        output_list = output_set2_list
                    elif set2_remaining == 0:
                        # Must be set 1
                        put_in, lst = set1_writer, set1_list
                        output_list = True
                    else:
                        # Randomly choose which set to put this doc in
                        set1_prob = float(set1_remaining) / (set1_remaining + set2_remaining)
                        use_set1 = random.random() < set1_prob

                        put_in, lst = (set1_writer, set1_list) if use_set1 else (set2_writer, set2_list)
                        output_list = use_set1 or output_set2_list

                    put_in.add_document(archive_name, doc_name, doc_data)
                    if output_list:
                        lst.append(doc_name)

        # Output the list(s) of chosen docs
        output_dir = self.info.get_absolute_output_dir("doc_list1")
        self.log.info("Outputting set1 list to %s" % output_dir)
        with StringListWriter(output_dir) as list_writer:
            list_writer.data = set1_list

        if output_set2_list:
            output_dir = self.info.get_absolute_output_dir("doc_list2")
            self.log.info("Outputting set2 list to %s" % output_dir)
            with StringListWriter(output_dir) as list_writer:
                list_writer.data = set2_list
