import StringIO
import os
import random
import shutil
import tarfile
from tempfile import mkdtemp
from traceback import format_exc

import cPickle as pickle

import zlib
from itertools import izip

from pimlico.datatypes.base import IterableCorpusWriter, InvalidDocument
from .base import IterableCorpus


class TarredCorpus(IterableCorpus):
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

    def archive_iter(self, subsample=None, start_after=None):
        gzip = self.metadata.get("gzip", False)
        # Prepare a temporary directory to extract everything to
        tmp_dir = mkdtemp()

        if start_after is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name)
            started = False

        try:
            for tar_name, tarball_filename in zip(self.tarballs, self.tar_filenames):
                # If we're waiting for a particular archive/file, we can skip archives until we're in the right one
                if not started and start_after[0] != tar_name:
                    continue

                # Extract the tarball to the temp dir
                with tarfile.open(tarball_filename, 'r') as tarball:
                    for tarinfo in tarball:
                        filename = tarinfo.name

                        # Allow the first portion of the corpus to be skipped
                        if not started:
                            # We know we're in the right archive now, skip until we get to the requested file
                            if start_after[1] == filename:
                                # We've hit the condition for starting
                                # Skip this doc and start on the next
                                started = True
                            continue

                        # If subsampling, decide whether to extract this file
                        if subsample is not None and random.random() > subsample:
                            # Reject this file
                            continue

                        tarball.extract(tarinfo, tmp_dir)
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
                            try:
                                document = self.process_document(document)
                            except BaseException, e:
                                # If there's any problem reading in the document, yield an invalid doc with the error
                                document = InvalidDocument("datatype %s reader" % self.datatype_name,
                                                           "%s: %s" % (e, format_exc()))
                        yield tar_name, filename, document
                        # Remove the file once we're done with it (when we request another)
                        os.remove(os.path.join(tmp_dir, filename))

                    # Catch the case where the archive/filename requested as a starting point wasn't found
                    # We only get here with started=False when we're in the right archive and have got through the
                    #  the whole thing without finding the requested filename
                    if not started:
                        raise TarredCorpusIterationError(
                            "tried to start iteration over tarred corpus at document (%s, %s), but filename %s "
                            "wasn't found in archive %s" % (start_after[0], start_after[1], start_after[1], tar_name)
                        )
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


class TarredCorpusWriter(IterableCorpusWriter):
    """
    If gzip=True, each document is gzipped before adding it to the archive. Not the same as creating a tarball,
    since the docs are gzipped *before* adding them, not the whole archive together, but it means we can easily
    iterate over the documents, unzipping them as required.

    A subtlety of TarredCorpusWriter and its subclasses is that, as soon as the writer has been initialized,
    it must be legitimate to initialize a datatype to read the corpus. Naturally, at this point there will
    be no documents in the corpus, but it allows us to do document processing on the fly by initializing
    writers and readers to be sure the pre/post-processing is identical to if we were writing the docs to disk
    and reading them in again.

    """
    def __init__(self, base_dir, gzip=False, append=False):
        super(TarredCorpusWriter, self).__init__(base_dir)
        self.append = append
        self.current_archive_name = None
        self.current_archive_tar = None
        self.doc_count = 0
        self.gzip = gzip
        # Set "gzip" in the metadata, so we know to unzip when reading
        self.metadata["gzip"] = gzip

        self.metadata["length"] = 0
        if append:
            # Try reading length so far if we're appending and some docs have already been written
            # If no metadata has been written, we start from 0
            metadata_path = os.path.join(self.base_dir, "corpus_metadata")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    self.metadata["length"] = pickle.load(f).get("length", 0)

        # Write out the metadata, so we're in a fit state to open a reader
        self.write_metadata()

    def add_document(self, archive_name, doc_name, data):
        data = self.document_to_raw_data(data)

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
            tar_filename = os.path.join(self.data_dir, "%s.tar" % archive_name)
            # If we're appending a corpus and the archive already exists, append to it
            try:
                self.current_archive_tar = tarfile.TarFile(tar_filename, mode="a" if self.append else "w")
            except tarfile.ReadError:
                # Couldn't open the existing file to append to, write instead
                self.current_archive_tar = tarfile.TarFile(tar_filename, mode="w")

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

    def document_to_raw_data(self, doc):
        """
        Overridden by subclasses to provide the mapping from the structured data supplied to the writer to
        the actual raw string to be written to disk. Override this instead of add_document(), so that filters
        can do the mapping on the fly without writing the output to disk.

        """
        return doc

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_archive_tar is not None:
            self.current_archive_tar.close()
        self.metadata["length"] = self.doc_count
        super(TarredCorpusWriter, self).__exit__(exc_type, exc_val, exc_tb)


def pass_up_invalid(fn):
    """
    Decorator for document_to_raw_data() methods of TarredCorpusWriter subclasses that detects invalid documents and
    calls simply returns them, skipping any subclass-specific processing. Does the same where the data
    is None.

    """
    def _fn(self, data):
        if type(data) is InvalidDocument or data is None:
            # Don't do subclass's processing
            return data
        else:
            return fn(self, data)
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

    def archive_iter(self, subsample=None, start_after=None):
        # Iterate over all tarred corpora at once
        for corpus_items in izip(
                *[corpus.archive_iter(subsample=None, start_after=start_after) for corpus in self.corpora]):
            # Check we've got the same archive and doc name combination from every corpus
            if not all(corpus_item[0] == corpus_items[0][0] for corpus_item in corpus_items[1:]) or \
                    not all(corpus_item[1] == corpus_items[0][1] for corpus_item in corpus_items[1:]):
                raise CorpusAlignmentError(
                    "filenames in tarred corpora do not correspond: %s" %
                    ", ".join(["(%s/%s)" % (corpus_item[0], corpus_item[1]) for corpus_item in corpus_items])
                )

            # If subsampling, decide whether to yield this file
            if subsample is not None and random.random() > subsample:
                continue

            yield corpus_items[0][0], corpus_items[0][1], [corpus_item[2] for corpus_item in corpus_items]

    def __len__(self):
        return len(self.corpora[0])


class CorpusAlignmentError(Exception):
    pass


class TarredCorpusIterationError(Exception):
    pass
