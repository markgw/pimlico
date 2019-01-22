import StringIO
import codecs
import os
import tarfile

import contextlib2

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
        tar_filename = self.info.options["tar"]

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with contextlib2.ExitStack() as exit_stack:
            if tar_filename is not None:
                if not tar_filename.endswith(".tar"):
                    tar_filename += ".tar"
                tar_path = os.path.join(output_path, tar_filename)
                self.log.info("Outputting corpus to tar archive: {}".format(tar_path))

                # Open the tar file
                tar_archive = tarfile.open(tar_path, "w")
                # Make sure the tarfile gets closed
                exit_stack.enter_context(tar_archive)
            else:
                self.log.info("Outputting corpus to {}".format(output_path))
                tar_archive = None

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

                # Prepare a filename for the doc
                filename = doc_name
                if filename_suffix is not None:
                    if "." in filename[-4:]:
                        filename = filename.rpartition(".")[0]
                    filename = "{}{}".format(filename, filename_suffix)

                if tar_archive is not None:
                    # No need to create subdirs in the tar file as we do on disk
                    if archive_dirs:
                        archive_dir = archive_name
                    else:
                        archive_dir = ""
                    doc_path = os.path.join(archive_dir, filename)

                    # Simply add the file to the archive
                    doc_data_enc = doc_data.encode("utf-8")
                    tar_info = tarfile.TarInfo(doc_path)
                    tar_info.size = len(doc_data_enc)
                    tar_archive.addfile(tar_info, StringIO.StringIO(doc_data_enc))
                else:
                    if archive_dirs:
                        archive_subdir = os.path.join(output_path, archive_name)
                        if archive_name not in created_archive_dirs:
                            # Create a new dir for this archive
                            if not os.path.exists(archive_subdir):
                                os.makedirs(archive_subdir)
                                created_archive_dirs.add(archive_subdir)
                    else:
                        archive_subdir = output_path

                    # Allow doc name to include a directory path as well as file basename
                    doc_path = os.path.split(doc_name)
                    if len(doc_path) > 1:
                        doc_dir_path = doc_path[:-1]
                        doc_name = doc_path[-1]

                        doc_dir = os.path.join(archive_subdir, *doc_dir_path)
                        if not os.path.exists(doc_dir):
                            os.makedirs(doc_dir)
                    else:
                        doc_dir = archive_subdir

                    # Output the document's data
                    with codecs.open(os.path.join(doc_dir, filename), "w", encoding="utf8") as f:
                        f.write(doc_data)

        self.log.info("Corpus written")
