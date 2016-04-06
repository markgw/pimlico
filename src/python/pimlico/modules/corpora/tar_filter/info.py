"""
Like tar, but doesn't write the archives to disk. Instead simulates the behaviour of
tar but as a filter, grouping files on the fly and passing them through with an archive name

"""
import random
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.execute import ModuleNotReadyError
from pimlico.datatypes.base import IterableCorpus
from pimlico.datatypes.tar import TarredCorpus


# Subclass TarredCorpus so that inputs expecting one can accept this
class TarredCorpusFilter(TarredCorpus):
    def __init__(self, pipeline, input_datatype, archive_size, archive_basename="archive"):
        IterableCorpus.__init__(self, None, pipeline)

        self.archive_basename = archive_basename
        self.input_datatype = input_datatype
        self.archive_size = archive_size

        self._tarballs = None

    def __len__(self):
        return len(self.input_datatype)

    def extract_file(self, archive_name, filename):
        raise TypeError("cannot extract files from filter: it's not an actual corpus")

    def __iter__(self):
        for __, doc_name, doc in self.archive_iter():
            yield doc_name, doc

    @property
    def tarballs(self):
        if not self.data_ready():
            raise ModuleNotReadyError("cannot work out the tarball names for a tarred corpus filter until its input "
                                      "data is ready")

        if self._tarballs is None:
            # Work out now what the archive names are going to look like and how many there will be
            total_archives = len(self) / self.archive_size

            # Work out how many digits to pad the archive numbers with in the filenames
            digits = len("%d" % (total_archives-1))
            # Prepare a formatter for archive numbers
            archive_name_format = "%s-%%%sd" % (self.archive_basename, "0" * digits)

            self._tarballs = [archive_name_format % archive_num for archive_num in range(total_archives)]
        return self._tarballs

    def archive_iter(self, subsample=None, start_after=None):
        tarballs = self.tarballs

        current_archive = 0
        current_archive_count = 0

        if start_after is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've skipped this number of docs or hit this (archive, doc name)
            started = False

        for file_num, (doc_name, doc) in enumerate(self.input_datatype):
            current_archive_count += 1

            # Allow the first portion of the corpus to be skipped
            if not started:
                if (type(start_after) is int and file_num == start_after) or \
                        (start_after == (tarballs[current_archive], doc_name)):
                    # We've hit the condition for starting
                    # Skip this doc and start on the next
                    started = True
                continue

            # If subsampling, decide whether to extract this file
            if subsample is not None and random.random() > subsample:
                # Reject this file
                continue

            # Check whether we've put enough files in the current archive to move onto the next
            if current_archive_count == self.archive_size:
                current_archive = min(len(tarballs), current_archive+1)
                current_archive_count = 0

            yield tarballs[current_archive], doc_name, doc

    def list_archive_iter(self):
        # Since we're not extracting the data here, we can't make things any faster in the case where the document
        #  itself isn't needed. Implement this for compatibility with TarredCorpus
        for tar_name, doc_name, doc in self.archive_iter():
            yield tar_name, doc_name

    def data_ready(self):
        return self.input_datatype.data_ready()


class ModuleInfo(BaseModuleInfo):
    module_type_name = "tar_extract"
    module_inputs = [("documents", IterableCorpus)]
    module_outputs = [("documents", TarredCorpusFilter)]
    module_options = [
        ("archive_size", {
            "help": "Number of documents to include in each archive (default: 1k)",
            "default": 1000,
        }),
        ("archive_basename", {
            "help": "Base name to use for archive tar files. The archive number is appended to this. "
                    "(Default: 'archive')",
            "default": "archive",
        }),
    ]
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype):
        if output_name == "documents":
            return TarredCorpusFilter(self.pipeline, self.get_input("documents"), self.options["archive_size"],
                                      archive_basename=self.options["archive_basename"])
        else:
            return super(ModuleInfo, self).instantiate_output_datatype(output_name, output_datatype)
