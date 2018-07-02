# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import cPickle as pickle
import gzip
import json
import os
import shutil
import tarfile
import zlib
from cStringIO import StringIO
from itertools import izip
from tempfile import mkdtemp

from pimlico.datatypes.corpora import IterableCorpusWriter, InvalidDocument
from pimlico.utils.filesystem import retry_open
from pimlico.datatypes.corpora import IterableCorpus

__all__ = [
    "GroupedCorpus", "AlignedGroupedCorpora",
    "CorpusAlignmentError", "GroupedCorpusIterationError"
]


class GroupedCorpus(IterableCorpus):
    datatype_name = "grouped_corpus"
    # This may be overridden by subclasses to provide filters for documents applied before main doc processing
    document_preprocessors = []

    def data_ready(self, base_dir):
        # Run the superclass check -- that the data dir exists
        # Also check that we've got at least one archive in the data dir
        return super(GroupedCorpus, self).data_ready(base_dir) and \
               len(self._get_archive_filenames(self._get_data_dir(base_dir))) > 0

    def _get_archive_filenames(self, data_dir):
        if data_dir is not None:
            return [f for f in
                    [os.path.join(root, filename) for root, dirs, files in os.walk(data_dir) for filename in files]
                    if f.endswith(".tar.gz") or f.endswith(".tar")]
        else:
            return []

    class Reader:
        def __init__(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)
            # Read in the archive filenames, which are stored as tar files
            self.archive_filenames = self.datatype._get_archive_filenames(self.data_dir)
            self.archive_filenames.sort()
            self.archives = [os.path.splitext(os.path.basename(f))[0] for f in self.archive_filenames]

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

        def doc_iter(self, start_after=None, skip=None, name_filter=None):
            for __, doc_name, doc in self.archive_iter(start_after=start_after, skip=skip, name_filter=name_filter):
                yield doc_name, doc

        def archive_iter(self, start_after=None, skip=None, name_filter=None):
            """
            Iterate over corpus archive by archive, yielding for each document the archive name,
            the document name and the document itself.

            :param name_filter: if given, should be a callable that takes two args, an archive name and
                document name, and returns True if the document should be yielded and False if it should be skipped.
                This can be preferable to filtering the yielded documents, as it skips all document pre-processing
                for skipped documents, so speeds up things like random subsampling of a corpus, where the
                document content never needs to be read in skipped cases
            :param start_after: skip over the first portion of the corpus, until the given document
                is reached. Should be specified as a pair (archive name, doc name)
            :param skip: skips over the first portion of the corpus, until this number of documents have
                been seen
            """
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
                for archive_name, archive_filename in zip(self.archives, self.archive_filenames):
                    if not started and start_after is not None:
                        if start_after[0] == archive_name and start_after[1] is None:
                            # Asked to start after an archive, but not given specific filename
                            # Skip the whole archive and start at the beginning of the next one
                            # Cancel the start_after requirement, but don't start yet, as we might still skip
                            start_after = None
                            continue
                        elif start_after[0] != archive_name:
                            # If we're waiting for a particular archive/file, skip archives until we're in the right one
                            continue

                    # Extract the tarball to the temp dir
                    with tarfile.open(archive_filename, fileobj=retry_open(archive_filename, mode="r")) as tarball:
                        for tarinfo in tarball:
                            filename = tarinfo.name
                            # By default, doc name is just the same as filename
                            # Filenames could be unicode and we should preserve that in the doc name
                            doc_name = filename.decode("utf8")

                            if gzipped and doc_name.endswith(".gz"):
                                # If we used the .gz extension while writing the file, remove it to get the doc name
                                doc_name = doc_name[:-3]

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

                            # If subsampling or filtering, decide whether to extract this file
                            if name_filter is not None and not name_filter(archive_name, doc_name):
                                # Reject this file
                                continue

                            tarball.extract(tarinfo, tmp_dir)
                            # Read in the data
                            with open(os.path.join(tmp_dir, filename), "r") as f:
                                raw_data = f.read()
                            if gzipped:
                                if doc_name.endswith(".gz"):
                                    # Gzipped document
                                    with gzip.GzipFile(fileobj=StringIO(raw_data), mode="rb") as gzip_file:
                                        raw_data = gzip_file.read()
                                else:
                                    # For backwards-compatibility, where gzip=True, but the gz extension wasn't used, we
                                    #  just decompress with zlib, without trying to parse the gzip headers
                                    raw_data = zlib.decompress(raw_data)
                            if encoding is not None:
                                raw_data = raw_data.decode(encoding)

                            # Apply subclass-specific post-processing and produce a document instance
                            document = self.data_to_document(raw_data)

                            yield archive_name, doc_name, document
                            # Remove the file once we're done with it (when we request another)
                            os.remove(os.path.join(tmp_dir, filename))

                        # Catch the case where the archive/filename requested as a starting point wasn't found
                        # We only get here with started=False when we're in the right archive and have got through the
                        #  the whole thing without finding the requested filename
                        if not started and start_after is not None:
                            raise GroupedCorpusIterationError(
                                "tried to start iteration over grouped corpus at document (%s, %s), but filename %s "
                                "wasn't found in archive %s" % (start_after[0], start_after[1], start_after[1], archive_name)
                            )
            finally:
                # Remove the temp dir
                shutil.rmtree(tmp_dir)

        def list_archive_iter(self):
            for archive_name, archive_filename in zip(self.archives, self.archive_filenames):
                tarball = tarfile.open(os.path.join(self.data_dir, archive_filename), 'r')
                filenames = tarball.getnames()
                for filename in filenames:
                    yield archive_name, filename


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

    TODO Turn this into a new-style writer

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


def pass_up_invalid(fn):
    """
    Decorator for document_to_raw_data() methods of TarredCorpusWriter subclasses that detects invalid documents and
    calls simply returns them, skipping any subclass-specific processing. Does the same where the data
    is None.

    TODO Use, modify, replace or remove for new writer

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


class AlignedGroupedCorpora(object):
    """
    Iterator for iterating over multiple corpora simultaneously that contain the same files, grouped into
    archives in the same way. This is the standard utility for taking multiple inputs to a Pimlico module
    that contain different data but for the same corpus (e.g. output of different tools).

    """
    def __init__(self, readers):
        if len(readers) == 0:
            raise CorpusAlignmentError("corpus aligner must have at least one corpus, got zero")

        self.readers = readers
        self.archives = self.readers[0].archives
        # Check that the corpora have the same archives in them
        if not all(c.archives == self.archives for c in self.readers):
            raise CorpusAlignmentError("not all corpora have the same archives in them, cannot align")

    def __iter__(self):
        for archive, filename, docs in self.archive_iter():
            yield filename, docs

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        # Iterate over all grouped corpora at once
        for corpus_items in izip(
                *[corpus.archive_iter(start_after=start_after, skip=skip)
                  for corpus in self.readers]):
            # Check we've got the same archive and doc name combination from every corpus
            if not all(corpus_item[0] == corpus_items[0][0] for corpus_item in corpus_items[1:]) or \
                    not all(corpus_item[1] == corpus_items[0][1] for corpus_item in corpus_items[1:]):
                raise CorpusAlignmentError(
                    "filenames within archives in grouped corpora do not correspond: %s" %
                    ", ".join(["(%s/%s)" % (corpus_item[0], corpus_item[1]) for corpus_item in corpus_items])
                )

            # If filtering, apply the filter only once for all corpora
            if name_filter is not None and not name_filter(corpus_items[0][0], corpus_items[0][1]):
                continue

            yield corpus_items[0][0], corpus_items[0][1], [corpus_item[2] for corpus_item in corpus_items]

    def __len__(self):
        return len(self.readers[0])


class CorpusAlignmentError(Exception):
    pass


class GroupedCorpusIterationError(Exception):
    pass
