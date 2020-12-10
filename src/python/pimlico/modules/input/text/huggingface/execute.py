import os
from builtins import str

from pimlico.utils.progress import get_progress_bar

from pimlico.modules.corpora.group.info import IterableCorpusGrouper

from pimlico.utils.core import multiwith

from pimlico.core.modules.execute import ModuleExecutionError

from pimlico.core.modules.base import BaseModuleExecutor

from datasets import load_dataset


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        opts = self.info.options
        dataset_name = opts["dataset"]
        dataset_config_name = opts["name"]
        dataset_split = opts["split"]
        columns = opts["columns"]
        doc_name_column = opts["doc_name"]

        # Use the output dir as a temporary location to download to
        with self.info.get_output_writer("default") as default_writer:
            download_dir = os.path.join(default_writer.data_dir, "download")

            self.log.info("Fetching {} dataset from Huggingface to {}".format(dataset_name, download_dir))
            dataset = load_dataset(
                dataset_name, name=dataset_config_name, split=dataset_split, cache_dir=download_dir,
                download_mode="reuse_dataset_if_exists"
            )

            # Check that the requested columns are available
            available_columns = dataset.column_names
            unavailable_columns = [col for col in columns if col not in available_columns]
            if unavailable_columns:
                raise ModuleExecutionError("requested column{} not available in downloaded dataset: {}".format(
                    "s" if len(unavailable_columns) > 1 else "",
                    ", ".join(unavailable_columns)
                ))
            if doc_name_column != "enum" and doc_name_column not in available_columns:
                raise ModuleExecutionError("requested column for doc names ({}) is not in the dataset"
                                           .format(doc_name_column))

            # Prepare all writers
            writers = [self.info.get_output_writer(col_name) for col_name in columns[1:]]
            all_writers = [default_writer] + writers
            grouper = IterableCorpusGrouper(1000, len(dataset))

            num_docs = len(dataset)
            self.log.info("Writing {:,} documents to Pimlico outputs".format(num_docs))
            pbar = get_progress_bar(num_docs, title="Writing")
            with multiwith(*writers):
                for doc_num, row in pbar(enumerate(dataset)):
                    doc_name = str(doc_num) if doc_name_column == "enum" else row[doc_name_column]
                    archive_name = grouper.next_document()

                    # The first column is always written to the default output
                    for col, writer in zip(columns, all_writers):
                        writer.add_document(archive_name, doc_name, {"text": str(row[col])})
