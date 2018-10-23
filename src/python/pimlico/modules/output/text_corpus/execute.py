import codecs
import os

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")
        output_path = self.info.options["path"]
        archive_dirs = self.info.options["archive_dirs"]
        filename_suffix = self.info.options["suffix"]
        invalid_action = self.info.options["invalid"]
        skip_invalid = invalid_action == "skip"

        if not os.path.exists(output_path):
            os.makedirs(output_path)
        self.log.info("Outputting corpus to {}".format(output_path))

        created_archive_dirs = set()

        pbar = get_progress_bar(len(corpus), title="Writing")
        for archive_name, doc_name, doc in pbar(corpus.archive_iter()):
            if is_invalid_doc(doc):
                if skip_invalid:
                    continue
                else:
                    doc_data = u""
            else:
                doc_data = doc.text

            if archive_dirs:
                archive_dir = os.path.join(output_path, archive_name)
                if archive_name not in created_archive_dirs:
                    # Create a new dir for this archive
                    if not os.path.exists(archive_dir):
                        os.makedirs(archive_dir)
                        created_archive_dirs.add(archive_dir)
            else:
                archive_dir = output_path

            # Allow doc name to include a directory path as well as file basename
            doc_path = os.path.split(doc_name)
            if len(doc_path) > 1:
                doc_dir_path = doc_path[:-1]
                doc_name = doc_path[-1]

                doc_dir = os.path.join(archive_dir, *doc_dir_path)
                if not os.path.exists(doc_dir):
                    os.makedirs(doc_dir)
            else:
                doc_dir = archive_dir

            # Prepare a filename for the doc
            filename = doc_name
            if filename_suffix is not None:
                if "." in filename[-4:]:
                    filename = filename.rpartition(".")[0]
                filename = "{}{}".format(filename, filename_suffix)

            # Output the document's data
            with codecs.open(os.path.join(doc_dir, filename), "w", encoding="utf8") as f:
                f.write(doc_data)

        self.log.info("Corpus written")
