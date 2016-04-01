import StringIO
import os
import random
import shutil
import tarfile
from tempfile import mkdtemp

import zlib
from itertools import izip

from pimlico.datatypes.base import IterableDocumentCorpusWriter, InvalidDocument
from .base import IterableDocumentCorpus


class TarredCorpus(IterableDocumentCorpus):
    datatype_name = "tar"
    # This may be overridden by subclasses to provide filters for documents applied before main doc processing
    document_preprocessors = []

    def __init__(self, base_dir, pipeline, raw_data=False):
        """
        If raw_data=True, post-processing of documents (as defined by subclasses) is not applied. Each
        document's text is just returned as read in from the file.
        """
        super(TarredCorpus, self).__init__(base_dir, pipeline)
        self.tar_filenames = [f for f in
                              [os.path.join(root, filename) for root, dirs, files in os.walk(self.data_dir)
                               for filename in files]
                              if f.endswith(".tar.gz") or f.endswith(".tar")]
        self.tar_filenames.sort()

        self.tarballs = [os.path.splitext(os.path.basename(f))[0] for f in self.tar_filenames]
        self.raw_data = raw_data

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
        gzip = self.metadata.get("gzip", False)
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
                        if gzip:
                            # Data was compressed with zlib while storing: decompress now
                            document = zlib.decompress(document)
                        document = document.decode("utf-8")
                        # Catch invalid documents
                        document = InvalidDocument.invalid_document_or_text(document)
                        # Apply subclass-specific post-processing if we've not been asked to yield just the raw data
                        if not self.raw_data and type(document) is not InvalidDocument:
                            document = self.process_document(document)
                        yield tar_name, filename, document
                        # Remove the file once we're done with it (when we request another)
                        os.remove(os.path.join(tmp_dir, filename))
        finally:
            # Remove the temp dir
            shutil.rmtree(tmp_dir)

    def process_document(self, data):
        """
        Process the data read in for a single document. Allows easy implementation of datatypes using
        TarredCorpus to do all the archive handling, etc, just specifying a particular way of handling
        the data within documents.

        By default, just returns the data string.

        """
        return data

    def list_archive_iter(self):
        for tar_name, tarball_filename in zip(self.tarballs, self.tar_filenames):
            tarball = tarfile.open(os.path.join(self.data_dir, tarball_filename), 'r')
            filenames = tarball.getnames()
            for filename in filenames:
                yield tar_name, filename

    def data_ready(self):
        # Run the superclass check -- that the data dir exists
        # Also check that we've got at least one tarball in the data dir
        return super(TarredCorpus, self).data_ready() and len(self.tar_filenames) > 0


class TarredCorpusWriter(IterableDocumentCorpusWriter):
    """
    If gzip=True, each document is gzipped before adding it to the archive. Not the same as creating a tarball,
    since the docs are gzipped *before* adding them, not the whole archive together, but it means we can easily
    iterate over the documents, unzipping them as required.

    """
    def __init__(self, base_dir, gzip=False):
        super(TarredCorpusWriter, self).__init__(base_dir)
        self.current_archive_name = None
        self.current_archive_tar = None
        self.doc_count = 0
        self.gzip = gzip
        # Set "gzip" in the metadata, so we know to unzip when reading
        self.metadata["gzip"] = gzip

    def add_document(self, archive_name, doc_name, data):
        if type(data) is InvalidDocument:
            # For an invalid result, signified by the special type, output the error info for later stages
            data = unicode(data)
        elif data is None:
            # For an empty result, signified by None, output an empty file
            data = u""

        if archive_name != self.current_archive_name:
            # Starting a new archive
            if self.current_archive_tar is not None:
                # Close the old one
                self.current_archive_tar.close()
            self.current_archive_name = archive_name
            self.current_archive_tar = tarfile.TarFile(os.path.join(self.data_dir, "%s.tar" % archive_name),
                                                       mode="w")

        # Keep a count of how many we've added so we can write metadata
        self.doc_count += 1

        # Add a new document to archive
        data = data.encode("utf-8")
        if self.gzip:
            data = zlib.compress(data, 9)
        data_file = StringIO.StringIO(data)
        info = tarfile.TarInfo(name=doc_name)
        info.size = len(data_file.buf)
        self.current_archive_tar.addfile(info, data_file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_archive_tar is not None:
            self.current_archive_tar.close()
        self.metadata["length"] = self.doc_count
        super(TarredCorpusWriter, self).__exit__(exc_type, exc_val, exc_tb)


def pass_up_invalid(fn):
    """
    Decorator for add_document() methods of TarredCorpusWriter subclasses that detects invalid documents and calls
    the superclass add_document() on them, skipping any subclass-specific processing. Does the same where the data
    is None.

    """
    def _fn(self, archive_name, doc_name, data):
        if type(data) is InvalidDocument or data is None:
            # Don't do subclass's processing
            return TarredCorpusWriter.add_document(self, archive_name, doc_name, data)
        else:
            return fn(self, archive_name, doc_name, data)
    return _fn


class AlignedTarredCorpora(object):
    """
    Iterator for iterating over multiple corpora simultaneously that contain the same files, grouped into
    archives in the same way. This is the standard utility for taking multiple inputs to a Pimlico module
    that contain different data but for the same corpus (e.g. output of different tools).

    """
    def __init__(self, corpora):
        if len(corpora) == 0:
            raise CorpusAlignmentError("corpus aligner must have at least one corpus, got zero")

        self.corpora = corpora
        self.tarballs = self.corpora[0].tarballs
        # Check that the corpora have the same tarballs in them
        if not all(c.tarballs == self.tarballs for c in self.corpora):
            raise CorpusAlignmentError("not all corpora have the same tarballs in them, cannot align")

    def __iter__(self):
        for archive, filename, docs in self.archive_iter():
            yield filename, docs

    def archive_iter(self):
        # Iterate over all tarred corpora at once
        for corpus_items in izip(*[corpus.archive_iter() for corpus in self.corpora]):
            # Check we've got the same archive and doc name combination from every corpus
            if not all(corpus_item[0] == corpus_items[0][0] for corpus_item in corpus_items[1:]) or \
                    not all(corpus_item[1] == corpus_items[0][1] for corpus_item in corpus_items[1:]):
                raise CorpusAlignmentError(
                    "filenames in tarred corpora do not correspond: %s" %
                    ", ".join(["(%s/%s)" % (corpus_item[0], corpus_item[1]) for corpus_item in corpus_items])
                )

            yield corpus_items[0][0], corpus_items[0][1], [corpus_item[2] for corpus_item in corpus_items]

    def __len__(self):
        return len(self.corpora[0])


class CorpusAlignmentError(Exception):
    pass
