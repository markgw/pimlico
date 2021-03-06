# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import cPickle as pickle
import gzip
import json
import os
import random
import shutil
import tarfile
import zlib
from cStringIO import StringIO
from itertools import izip
from tempfile import mkdtemp

from pimlico.old_datatypes.base import IterableCorpusWriter, InvalidDocument, DynamicInputDatatypeRequirement
from pimlico.old_datatypes.documents import RawDocumentType, RawTextDocumentType
from pimlico.utils.filesystem import retry_open
from .base import IterableCorpus

__all__ = [
    "TarredCorpus", "TarredCorpusWriter", "AlignedTarredCorpora",
    "CorpusAlignmentError", "TarredCorpusIterationError"
]


class TarredCorpus(IterableCorpus):
    datatype_name = "tar"
    # This may be overridden by subclasses to provide filters for documents applied before main doc processing
    document_preprocessors = []
    data_point_type = RawDocumentType

    def __init__(self, base_dir, pipeline, **kwargs):
        """
        If raw_data=True, post-processing of documents (as defined by subclasses) is not applied. Each
        document's text is just returned as read in from the file.
        """
        super(TarredCorpus, self).__init__(base_dir, pipeline, **kwargs)
        if self.data_dir is not None:
            self.tar_filenames = [f for f in
                                  [os.path.join(root, filename) for root, dirs, files in os.walk(self.data_dir)
                                   for filename in files]
                                  if f.endswith(".tar.gz") or f.endswith(".tar")]
            self.tar_filenames.sort()
            self.tarballs = [os.path.splitext(os.path.basename(f))[0] for f in self.tar_filenames]
        else:
            self.tar_filenames = []
            self.tarballs = []

    def extract_file(self, archive_name, filename):
        """
        Extract an individual file by archive name and filename. This is not an efficient
        way of extracting a lot of files. The typical use case of a tarred corpus is to
        iterate over its files, which is much faster.

        """
        with tarfile.open(os.path.join(self.data_dir, archive_name)) as archive:
            return archive.extractfile(filename).read()

    def __iter__(self):
        return self.doc_iter()

    def doc_iter(self, subsample=None, start_after=None, skip=None):
        for __, doc_name, doc in self.archive_iter(subsample=subsample, start_after=start_after, skip=skip):
            yield doc_name, doc

    def archive_iter(self, subsample=None, start_after=None, skip=None):
        gzipped = self.metadata.get("gzip", False)
        encoding = self.metadata.get("encoding", "utf-8")
        # Prepare a temporary directory to extract everything to
        tmp_dir = mkdtemp()

        skipped = 0
        if start_after is None and skip is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name), or after we've passed a certain number of docs
            started = False

        try:
            for tar_name, tarball_filename in zip(self.tarballs, self.tar_filenames):
                if not started and start_after is not None:
                    if start_after[0] == tar_name and start_after[1] is None:
                        # Asked to start after an archive, but not given specific filename
                        # Skip the whole archive and start at the beginning of the next one
                        # Cancel the start_after requirement, but don't start yet, as we might still skip
                        start_after = None
                        continue
                    elif start_after[0] != tar_name:
                        # If we're waiting for a particular archive/file, skip archives until we're in the right one
                        continue

                # Extract the tarball to the temp dir
                with tarfile.open(tarball_filename, fileobj=retry_open(tarball_filename, mode="r")) as tarball:
                    for tarinfo in tarball:
                        filename = tarinfo.name
                        # By default, doc name is just the same as filename
                        # Filenames could be unicode and we should preserve that in the doc name
                        doc_name = filename.decode("utf8")

                        # Allow the first portion of the corpus to be skipped
                        if not started:
                            if start_after is not None:
                                # We know we're in the right archive now, skip until we get to the requested file
                                if start_after[1] == filename:
                                    # We've hit the condition for starting
                                    # Skip this doc and start on the next (or after we've satisfied "skip")
                                    start_after = None
                                continue
                            elif skip is not None:
                                if skipped >= skip:
                                    # Skipped enough now: stop skipping
                                    started = True
                                else:
                                    # Keep skipping docs
                                    skipped += 1
                                    continue
                            else:
                                # No more skipping requirements left
                                started = True

                        # If subsampling, decide whether to extract this file
                        if subsample is not None and random.random() > subsample:
                            # Reject this file
                            continue

                        tarball.extract(tarinfo, tmp_dir)
                        # Read in the data
                        with open(os.path.join(tmp_dir, filename), "r") as f:
                            document = f.read()
                        if gzipped:
                            if doc_name.endswith(".gz"):
                                # If we used the .gz extension while writing the file, remove it to get the doc name
                                doc_name = doc_name[:-3]
                                with gzip.GzipFile(fileobj=StringIO(document), mode="rb") as gzip_file:
                                    document = gzip_file.read()
                            else:
                                # For backwards-compatibility, where gzip=True, but the gz extension wasn't used, we
                                #  just decompress with zlib, without trying to parse the gzip headers
                                document = zlib.decompress(document)
                        if encoding is not None:
                            document = document.decode(encoding)

                        if self.raw_data:
                            # Catch invalid documents, but otherwise do no processing
                            document = InvalidDocument.invalid_document_or_text(document)
                        else:
                            # Apply subclass-specific post-processing if we've not been asked to yield just the raw data
                            document = self.process_document_data_with_datatype(document)

                        yield tar_name, doc_name, document
                        # Remove the file once we're done with it (when we request another)
                        os.remove(os.path.join(tmp_dir, filename))

                    # Catch the case where the archive/filename requested as a starting point wasn't found
                    # We only get here with started=False when we're in the right archive and have got through the
                    #  the whole thing without finding the requested filename
                    if not started and start_after is not None:
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

        By default, uses the document data processing provided by the document type.

        Most of the time, you shouldn't need to override this, but just write a document type that does the
        necessary processing.

        I think we should remove this once the new (forthcoming) datatype system is ready, but
        we'll need to check that there's not still a use case for it.

        """
        return self.data_point_type_instance.process_document(data)

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

    If append=True, existing archives and their files are not overwritten, the new files are just added to the end.
    This is useful where we want to restart processing that was broken off in the middle. If trust_length=True,
    when appending the initial length of the corpus is read from the metadata already written. Otherwise (default),
    the number of docs already written is actually counted during initialization. This is sensible when the
    previous writing process may have ended abruptly, so that the metadata is not reliable. If you know you can
    trust the metadata, however, setting trust_length=True will speed things up.

    """
    def __init__(self, base_dir, gzip=False, append=False, trust_length=False, encoding="utf-8", **kwargs):
        super(TarredCorpusWriter, self).__init__(base_dir, **kwargs)
        self.append = append
        self.current_archive_name = None
        self.current_archive_tar = None
        self.gzip = gzip
        # Set "gzip" in the metadata, so we know to unzip when reading
        self.metadata["gzip"] = gzip
        self.encoding = encoding
        self.metadata["encoding"] = encoding

        self.metadata["length"] = 0
        if append:
            if trust_length:
                # Try reading length so far if we're appending and some docs have already been written
                # If no metadata has been written, we start from 0
                metadata_path = os.path.join(self.base_dir, "corpus_metadata")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        raw_data = f.read()
                        if len(raw_data) != 0:
                            # If empty metadata file, assume empty metadata
                            try:
                                # In later versions of Pimlico, we store metadata as JSON
                                data = json.loads(raw_data)
                            except ValueError:
                                # If the metadata was written by an earlier Pimlico version, it's a pickled dictionary
                                data = pickle.loads(raw_data)
                            self.metadata["length"] = data.get("length", 0)
            else:
                # Can't rely on the metadata: count up docs in archive to get initial length
                for root, dirs, files in os.walk(self.data_dir):
                    for filename in files:
                        tar_filename = os.path.join(root, filename)
                        if tar_filename.endswith(".tar.gz") or tar_filename.endswith(".tar"):
                            with tarfile.open(tar_filename, "r") as tarball:
                                self.metadata["length"] += len(tarball.getmembers())
        self.doc_count = self.metadata["length"]

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

        # Add a new document to archive
        if self.encoding is not None:
            data = data.encode(self.encoding)
        if self.gzip:
            # We used to just use zlib to compress, which works fine, but it's not easy to open the files manually
            # Using gzip (i.e. writing gzip headers) makes it easier to use the data outside Pimlico
            gzip_io = StringIO()
            with gzip.GzipFile(mode="wb", compresslevel=9, fileobj=gzip_io) as gzip_file:
                gzip_file.write(data)
            data = gzip_io.getvalue()
        data_file = StringIO(data)
        # If we're zipping, add the .gz extension, so it's easier to inspect the output manually
        info = tarfile.TarInfo(name="%s.gz" % doc_name if self.gzip else doc_name)
        info.size = len(data)
        self.current_archive_tar.addfile(info, data_file)

        # Keep a count of how many we've added so we can write metadata
        self.doc_count += 1

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


class RawTextTarredCorpus(TarredCorpus):
    datatype_name = "raw_text_tarred_corpus"
    data_point_type = RawTextDocumentType


class TarredCorpusType(DynamicInputDatatypeRequirement):
    """
    Input requirement for a TarredCorpus (or subclass) with a particular document type (or subclass).
    Should generally be used in input requirements in preference to giving specific subclasses of TarredCorpus
    that have a customized document type.

    """
    def __init__(self, *document_types):
        self.document_types = document_types
        self.datatype_doc_info = "TarredCorpus<%s>" % "|".join(dt.__name__ for dt in document_types)

    def type_checking_name(self):
        return self.datatype_doc_info

    def check_type(self, supplied_type):
        if isinstance(supplied_type, type):
            main_type_check = issubclass(supplied_type, TarredCorpus)
        else:
            main_type_check = isinstance(supplied_type, TarredCorpus)
        return main_type_check and issubclass(supplied_type.data_point_type, self.document_types)


def tarred_corpus_with_data_point_type(data_point_type):
    """
    Dynamically subclass TarredCorpus to provide a version with a given data-point type.
    Most of the time, static subclasses are provided and set their data-point type appropriately, but occasionally
    for type-checking purposes it can be useful to construct a new, specialized tarred corpus on the fly.

    """
    return type(
        "%sTarredCorpus" % data_point_type.__name__,
        (TarredCorpus,),
        dict(data_point_type=data_point_type),
    )


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


def exclude_invalid(doc_iter):
    """
    Generator that skips any invalid docs when iterating over a document dataset.

    """
    return ((doc_name, doc) for (doc_name, doc) in doc_iter if not isinstance(doc, InvalidDocument))


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
