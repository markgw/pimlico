import os
import random
import shutil
import tarfile
from tempfile import mkdtemp
from .base import IterableDocumentCorpus
from pimlico.datatypes.base import IterableDocumentCorpusWriter


class TarredCorpus(IterableDocumentCorpus):
    def __init__(self, base_dir):
        super(TarredCorpus, self).__init__(base_dir)
        self.tar_filenames = [f for f in
                              [os.path.join(root, filename) for root, dirs, files in os.walk(self.data_dir)
                               for filename in files]
                              if f.endswith(".tar.gz") or f.endswith(".tar")]
        self.tar_filenames.sort()

        self.tarballs = [os.path.basename(f) for f in self.tar_filenames]

    def extract_file(self, archive_name, filename):
        """
        Extract an individual file by archive name and filename. This is not an efficient
        way of extracting a lot of files. The typical use case of a tarred corpus is to
        iterate over its files, which is much faster.

        """
        with tarfile.open(os.path.join(self.data_dir, archive_name)) as archive:
            return archive.extractfile(filename).read()

    def __iter__(self):
        for __, doc_name, doc in self.archive_iter():
            yield doc_name, doc

    def archive_iter(self, subsample=None, start=0):
        # Prepare a temporary directory to extract everything to
        tmp_dir = mkdtemp()
        file_num = -1
        try:
            for tar_name, tarball_filename in zip(self.tarballs, self.tar_filenames):
                # Extract the tarball to the temp dir
                with tarfile.open(tarball_filename, 'r') as tarball:
                    for tarinfo in tarball:
                        file_num += 1
                        # Allow the first portion of the corpus to be skipped
                        if file_num < start:
                            continue
                        # If subsampling, decide whether to extract this file
                        if subsample is not None and random.random() > subsample:
                            # Reject this file
                            continue
                        tarball.extract(tarinfo, tmp_dir)
                        filename = tarinfo.name
                        # Read in the data
                        with open(os.path.join(tmp_dir, filename), "r") as f:
                            document = f.read()
                        yield tar_name, filename, document
                        # Remove the file once we're done with it (when we request another)
                        os.remove(os.path.join(tmp_dir, filename))
        finally:
            # Remove the temp dir
            shutil.rmtree(tmp_dir)

    def list_archive_iter(self):
        for tar_name, tarball_filename in zip(self.tarballs, self.tar_filenames):
            tarball = tarfile.open(os.path.join(self.data_dir, tarball_filename), 'r')
            filenames = tarball.getnames()
            for filename in filenames:
                yield tar_name, filename


class TarredCorpusWriter(IterableDocumentCorpusWriter):
    def __init__(self, *args, **kwargs):
        super(TarredCorpusWriter, self).__init__(*args, **kwargs)
        self.current_archive_name = None
        self.current_archive_tar = None
        self.doc_count = 0

    def add_document(self, archive_name, doc_name, data):
        if archive_name != self.current_archive_name:
            # Starting a new archive
            if self.current_archive_tar is not None:
                # Close the old one
                self.current_archive_tar.close()
            self.current_archive_name = archive_name
            self.current_archive_tar = tarfile.TarFile(os.path.join(self.data_dir, "%s.tar" % archive_name),
                                                       mode="w")
            # TODO Finish writing

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_archive_tar is not None:
            self.current_archive_tar.close()


class AlignedTarredCorpora(object):
    """
    Iterator for iterating over multiple corpora simultaneously that contain the same files, grouped into
    archives in the same way. This is the standard utility for taking multiple inputs to a Pimlico module
    that contain different data but for the same corpus (e.g. output of different tools).

    """
    def __init__(self, corpora):
        self.corpora = corpora
        self.data_dirs = [corpus.data_dir for corpus in corpora]
        self.tarballs = self.corpora[0].tarballs
        # Check that the corpora have the same tarballs in them
        if not all(c.tarballs == self.tarballs for c in self.corpora):
            raise CorpusAlignmentError("not all corpora have the same tarballs in them, cannot align: %s" %
                                       ", ".join(self.data_dirs))

    def __iter__(self):
        # Prepare a temporary directory to extract everything to
        tmp_dir = mkdtemp()
        try:
            # We know that each corpus has the same tarballs
            for tarball_filename in self.tarballs:
                # Don't extract the tar files: just iterate over them
                corpus_tars = [
                    tarfile.open(os.path.join(corpus.data_dir, tarball_filename), 'r') for corpus in self.corpora
                ]

                # Iterate over the untarred files: we assume all the files in the first corpus are also available
                # in the others
                for tarinfos in zip(*corpus_tars):
                    filename = tarinfos[0].name
                    if tarinfos[0].isdir():
                        # If this is a directory, we don't extract it: its files will show up as separate tarinfos
                        continue

                    if not all(tarinfo.name == filename for tarinfo in tarinfos):
                        raise IOError("filenames in tarballs (%s in %s) do not correspond: %s" %
                                      (tarball_filename,
                                       ", ".join(corpus.data_dir for corpus in self.corpora),
                                       ", ".join(tarinfo.name for tarinfo in tarinfos)))

                    documents = []
                    for tarball, tarinfo in zip(corpus_tars, tarinfos):
                        documents.append(tarball.extractfile(tarinfo).read())

                    # Just a single file
                    yield filename, documents
        finally:
            # Remove the temp dir
            shutil.rmtree(tmp_dir)

    def __len__(self):
        return len(self.corpora[0])


class CorpusAlignmentError(Exception):
    pass
