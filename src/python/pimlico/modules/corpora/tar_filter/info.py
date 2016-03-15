"""
Like tar, but doesn't write the archives to disk. Instead simulates the behaviour of
tar but as a filter, grouping files on the fly and passing them through with an archive name

"""
import random
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import IterableDocumentCorpus
from pimlico.datatypes.tar import TarredCorpus


# Subclass TarredCorpus so that inputs expecting one can accept this
class TarredCorpusFilter(TarredCorpus):
    def __init__(self, input_datatype, archive_size, archive_basename="archive"):
        IterableDocumentCorpus.__init__(self, None)

        # Work out now what the archive names are going to look like and how many there will be
        self.input_datatype = input_datatype
        self.archive_size = archive_size
        total_archives = len(self) / archive_size

        # Work out how many digits to pad the archive numbers with in the filenames
        digits = len("%d" % (total_archives-1))
        # Prepare a formatter for archive numbers
        archive_name_format = "%s-%%%sd" % (archive_basename, "0" * digits)
        # TODO Check these do the right thing
        self.tarballs = [archive_name_format % archive_num for archive_num in range(total_archives)]
        self.tar_filenames = ["%s.tar" % tarball for tarball in self.tarballs]

    def __len__(self):
        return len(self.input_datatype)

    def extract_file(self, archive_name, filename):
        raise TypeError("cannot extract files from filter: it's not an actual corpus")

    def __iter__(self):
        for __, doc_name, doc in self.archive_iter():
            yield doc_name, doc

    def archive_iter(self, subsample=None, start=0):
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

            yield self.tarballs[current_archive], doc_name, doc

    def list_archive_iter(self):
        # Since we're not extracting the data here, we can't make things any faster in the case where the document
        #  itself isn't needed. Implement this for compatibility with TarredCorpus
        for tar_name, doc_name, doc in self.archive_iter():
            yield tar_name, doc_name


class ModuleInfo(BaseModuleInfo):
    module_type_name = "tar_extract"
    module_inputs = [("documents", IterableDocumentCorpus)]
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

    def instantiate_output_datatype(self, output_name, output_datatype):
        if output_name == "documents":
            return TarredCorpusFilter(self.get_input("documents"), self.options["archive_size"],
                                      archive_basename=self.options["archive_basename"])
        else:
            return super(ModuleInfo, self).instantiate_output_datatype(output_name, output_datatype)
