import os
import shutil
from itertools import islice

from pimlico.utils.progress import get_progress_bar

from pimlico.modules.corpora.group.info import IterableCorpusGrouper

from sklearn.datasets import fetch_20newsgroups

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        opts = self.info.options

        # Use the output dir as a temporary location to download to
        with self.info.get_output_writer("text") as text_writer:
            with self.info.get_output_writer("labels") as label_writer:
                download_dir = os.path.join(text_writer.data_dir, "download")

                self.log.info("Fetching 20 Newsgroups data")
                data = fetch_20newsgroups(
                    data_home=download_dir, subset=opts["subset"], shuffle=opts["shuffle"],
                    random_state=opts["random_state"], remove=opts["remove"],
                )

                self.log.info("Fetched set contains {:,} documents".format(len(data.data)))

                if opts["limit"] is None:
                    length = len(data.data)
                else:
                    length = min(len(data.data), opts["limit"])
                length_limit = None if len(data.data) == length else length
                if length_limit is not None:
                    self.log.info("Limiting set to {:,} documents".format(length_limit))

                grouper = IterableCorpusGrouper(1000, len(data.data))
                _used = set()
                self.log.info("Writing as Pimlico corpora")
                pbar = get_progress_bar(length, title="Writing")
                for filename, text, label, archive_name in pbar(islice(
                        zip(data.filenames, data.data, data.target, grouper), length_limit)):
                    # The last two parts of the file path - newsgroup and number - uniquely
                    #  identify the doc
                    parts = filename.split("/")
                    doc_name = "{}/{}".format(parts[-2], parts[-1])
                    # Double-check this is unique
                    if doc_name in _used:
                        print("DUPLICATE", doc_name)
                    _used.add(doc_name)

                    text_writer.add_document(archive_name, doc_name, text_writer.datatype.data_point_type(text=text))
                    label_writer.add_document(archive_name, doc_name, label_writer.datatype.data_point_type(val=label))

                # Remove the downloaded files once we've extract the data we need
                shutil.rmtree(download_dir)
