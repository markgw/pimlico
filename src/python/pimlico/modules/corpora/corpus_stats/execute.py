import json
from collections import Counter

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.files import NamedFileWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")

        self.log.info("Counting tokens")
        pbar = get_progress_bar(len(corpus), title="Counting")
        token_count = Counter(token for doc_name, doc in pbar(corpus) if type(doc) is not InvalidDocument
                              for sent in doc for token in sent)

        types = len(token_count)
        tokens = sum(token_count.values())

        self.log.info("{:,} types".format(types))
        self.log.info("{:,} tokens".format(tokens))

        self.log.info("Counting sentences")
        pbar = get_progress_bar(len(corpus), title="Counting")
        sent_count = sum(len(doc) for doc_name, doc in pbar(corpus) if type(doc) is not InvalidDocument)

        self.log.info("{:,} sentences".format(sent_count))

        data = {
            "types": types,
            "tokens": tokens,
            "sentences": sent_count,
        }

        with NamedFileWriter(self.info.get_absolute_output_dir("stats"), "stats.json") as writer:
            writer.write_data(json.dumps(data, indent=4))
            self.log.info("Stats output to %s" % writer.absolute_path)
