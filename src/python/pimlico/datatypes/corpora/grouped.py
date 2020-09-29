# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from __future__ import absolute_import
from __future__ import print_function

import warnings

from future import standard_library

from pimlico.utils.pimarc import PimarcReader, PimarcWriter
from pimlico.utils.pimarc.reader import StartAfterFilenameNotFound
from pimlico.utils.pimarc.tar import PimarcTarBackend

standard_library.install_aliases()
from builtins import zip
from builtins import next
from builtins import object
from builtins import bytes

import pickle
import gzip
import json
import os
import zlib
from io import StringIO, BytesIO, open

from pimlico.datatypes.base import DynamicOutputDatatype
from pimlico.datatypes.corpora import IterableCorpus, DataPointType
from pimlico.datatypes.corpora.data_points import is_invalid_doc

__all__ = [
    "GroupedCorpus", "AlignedGroupedCorpora",
    "CorpusAlignmentError", "GroupedCorpusIterationError",
    "GroupedCorpusWithTypeFromInput", "CorpusWithTypeFromInput"
]


class GroupedCorpus(IterableCorpus):
    datatype_name = "grouped_corpus"
    # This may be overridden by subclasses to provide filters for documents applied before main doc processing
    document_preprocessors = []

    class Reader(object):
        class Setup(object):
            def data_ready(self, base_dir):
                # Run the superclass check -- that the data dir exists
                if not super(GroupedCorpus.Reader.Setup, self).data_ready(base_dir):
                    return False
                # Also check that we've got at least one archive in the data dir, unless the length of the corpus is 0
                if self.read_metadata(base_dir)["length"] > 0 and not self._has_archives(self._get_data_dir(base_dir)):
                    return False
                return True

            @classmethod
            def _get_archive_filenames(cls, data_dir):
                return list(cls._iter_archive_filenames(data_dir))

            @classmethod
            def _iter_archive_filenames(cls, data_dir):
                if data_dir is None:
                    return
                else:
                    # Check for any .prc files: if even one is found, we look only at .prc files
                    ext = ".prc" if cls._uses_prc(data_dir) else ".tar"
                    for root, dirs, files in os.walk(data_dir):
                        for filename in files:
                            if filename.endswith(ext):
                                yield os.path.join(root, filename)

            @classmethod
            def _uses_prc(cls, data_dir):
                found_tar = False
                for root, dirs, files in os.walk(data_dir):
                    for filename in files:
                        if filename.endswith(".prc"):
                            # Found one prc file, so use prc
                            return True
                        elif filename.endswith(".tar"):
                            # Found one tar file: if no prc files found, we're clearly using tar
                            found_tar = True
                # No archives found:
                # If tars found, use them
                # Otherwise, assume we're using prc but don't have any files yet
                return not found_tar

            def _has_archives(self, data_dir):
                # Return True if there's at least 1 archive in the dir
                try:
                    next(self._iter_archive_filenames(data_dir))
                except StopIteration:
                    return False
                else:
                    return True

        def __init__(self, *args, **kwargs):
            super(GroupedCorpus.Reader, self).__init__(*args, **kwargs)
            # Read in the archive filenames, which are stored as tar files
            self.archive_filenames = self.setup._get_archive_filenames(self.data_dir)
            self.archive_filenames.sort()
            self.archives = [os.path.splitext(os.path.basename(f))[0] for f in self.archive_filenames]
            self.archive_to_archive_filename = dict(zip(self.archives, self.archive_filenames))
            # Whether this corpus uses Pimarc (prc) files or tar
            self.uses_tar = not self.setup._uses_prc(self.data_dir)

            # Cache the last-used archive
            self._last_used_archive = None
            self._last_used_archive_name = None

        def get_archive(self, archive_name):
            """
            Return a `PimarcReader` for the named archive, or, if using the tar backend, a
            PimarcTarBackend.

            """
            if self._last_used_archive_name is None or self._last_used_archive_name != archive_name or \
                    self._last_used_archive.closed:
                archive_filename = self.archive_to_archive_filename[archive_name]
                archive_path = os.path.join(self.data_dir, archive_filename)
                if archive_filename.endswith(".tar"):
                    # Use the tar backend for backwards compatibility
                    arc = PimarcTarBackend(archive_path)
                else:
                    arc = PimarcReader(archive_path)

                # Close the cached archive
                if self._last_used_archive is not None:
                    self._last_used_archive.close()
                # Replace it with the new one
                self._last_used_archive_name = archive_name
                self._last_used_archive = arc

            # Used the cached archive
            return self._last_used_archive

        def extract_file(self, archive_name, filename):
            """
            Extract an individual file by archive name and filename.

            With the old use of tar to store file, this was not an efficient
            way of extracting a lot of files. The typical use case of a grouped corpus is to
            iterate over its files, which is much faster.

            Now we're using Pimarc, this is faster. However, jumping a lot between different
            archives is still slow, as you have to load the index for each archive. A
            better approach is to load an archive and extract all the files from it you
            need before loading another.

            The reader will cache the most recently used archive, so if you use this method
            multiple times with the same archive name, it won't reload the index in between.

            """
            __, file_data = self.get_archive(archive_name)[filename]
            return file_data

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
            if skip is not None and skip < 1:
                skip = None

            # -1 means don't skip anything, otherwise we accumulate how many we've skipped
            skipped = -1 if skip is None else 0
            # Start after we've hit this (archive, doc name)
            started = start_after is None
            start_after_req = start_after

            for archive_name in self.archives:
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

                # Now we're either reading the whole of this archive, or starting after a filename in it
                with self.get_archive(archive_name) as archive:
                    skip_in_archive = None
                    start_after_in_archive = None
                    # Allow the first portion of the corpus to be skipped
                    if start_after is not None:
                        # If we've got this far, we're in the right archive, but need to skip past the filename
                        start_after_in_archive = start_after[1]
                        start_after = None
                        started = True
                    elif skipped != -1:
                        # If we're skipping a certain number of docs, check how long the archive is to know
                        # whether to skip it all
                        # This is slow for tar, but relatively fast for Pimarc
                        archive_length = len(archive)
                        if skipped + archive_length <= skip:
                            # We can skip the whole of this archive
                            skipped += archive_length
                            continue
                        else:
                            # Skip over the remaining number within this archive
                            skip_in_archive = skip - skipped
                            # Don't skip at all in future archives
                            skipped = -1

                    try:
                        # Iterate over the files in the archive
                        for metadata, raw_data in archive.iter_files(
                                skip=skip_in_archive, start_after=start_after_in_archive):
                            filename = metadata["name"]
                            # By default, doc name is just the same as filename
                            doc_name = filename
                            if gzipped and doc_name.endswith(".gz"):
                                # If we used the .gz extension while writing the file, remove it to get the doc name
                                doc_name = doc_name[:-3]

                            # If subsampling or filtering, decide whether to extract this file
                            if name_filter is not None and not name_filter(archive_name, doc_name):
                                # Reject this file
                                continue

                            if gzipped:
                                if doc_name.endswith(".gz"):
                                    # Gzipped document
                                    with gzip.GzipFile(fileobj=BytesIO(raw_data), mode="rb") as gzip_file:
                                        raw_data = gzip_file.read()
                                else:
                                    # For backwards-compatibility, where gzip=True, but the gz extension wasn't used, we
                                    #  just decompress with zlib, without trying to parse the gzip headers
                                    raw_data = zlib.decompress(raw_data)

                            # Apply subclass-specific post-processing and produce a document instance
                            document = self.data_to_document(raw_data)

                            yield archive_name, doc_name, document

                    except StartAfterFilenameNotFound:
                        # Catch the case where the archive/filename requested as a starting point wasn't found
                        # With Pimarc, the error is raised immediately
                        # With tar, it's only raised when we get to the end of the file without finding the filename
                        raise GroupedCorpusIterationError(
                            "tried to start iteration over grouped corpus at document (%s, %s), but filename %s "
                            "wasn't found in archive %s" %
                            (start_after_req[0], start_after_req[1], start_after_req[1], archive_name)
                        )

        def list_archive_iter(self):
            gzipped = self.metadata.get("gzip", False)
            for archive_name in self.archives:
                with self.get_archive(archive_name) as archive:
                    for filename in archive.iter_filenames():
                        # Do the same name preprocessing that archive_iter does
                        doc_name = filename
                        if gzipped and doc_name.endswith(".gz"):
                            # If we used the .gz extension while writing the file, remove it to get the doc name
                            doc_name = doc_name[:-3]
                        yield archive_name, doc_name

        def list_iter(self):
            """
            Iterate over the list of document names, without processing the doc contents.

            In some cases, this could be considerably faster than iterating over all the docs.

            """
            for archive_name, doc_name in self.list_archive_iter():
                yield doc_name

    class Writer(object):
        """
        Writes a large corpus of documents out to disk, grouping them together in Pimarc archives.

        A subtlety is that, as soon as the writer has been initialized,
        it must be legitimate to initialize a datatype to read the corpus. Naturally, at this point there will
        be no documents in the corpus, but it allows us to do document processing on the fly by initializing
        writers and readers to be sure the pre/post-processing is identical to if we were writing the docs to disk
        and reading them in again.

        The reader above allows reading from tar archives for backwards compatibility. However,
        it is no longer possible to write corpora to tar archives. This has been completely replaced
        by the new Pimarc archives, which are more efficient to use and allow random access when
        necessary without huge speed penalties.

        """
        metadata_defaults = {
            "gzip": (
                False,
                "Gzip each document before adding it to the archive. Not the same as creating a tarball, "
                "since the docs are gzipped *before* adding them, not the whole archive together, but means "
                "we can easily iterate over the documents, unzipping them as required"
            ),
        }
        writer_param_defaults = {
            "append": (
                False,
                "If True, existing archives and their files are not overwritten, the new files are "
                "just added to the end. This is useful where we want to restart processing that was "
                "broken off in the middle"
            ),
        }

        def __init__(self, *args, **kwargs):
            super(GroupedCorpus.Writer, self).__init__(*args, **kwargs)

            # Set "gzip" in the metadata, so we know to unzip when reading
            self.gzip = self.metadata["gzip"]
            self.append = self.params["append"]

            self.current_archive_name = None
            self.current_archive = None

            self.metadata["length"] = 0

            if self.append:
                # Shouldn't rely on the metadata: count up docs in archive to get initial length
                # This can take a long time on a large corpus
                self.metadata["length"] = self._count_written_docs()
            self.doc_count = self.metadata["length"]

        def add_document(self, archive_name, doc_name, doc, metadata=None):
            """
            Add a document to the named archive. All docs should be added to a single archive
            before moving onto the next. If the archive name is the same as the previous
            doc added, the doc's data will be appended. Otherwise, the archive is finalized
            and we move onto the new archive.
            
            :param metadata: dict of metadata values to write with the document. If doc is a document
                instance, the metadata is taken from there first, but these values will override anything
                in the doc object's metadata. If doc is a bytes object, the metadata kwarg is used
            :param archive_name: archive name
            :param doc_name: name of document
            :param doc: document instance or bytes object containing document's raw data
            """
            # A document instance provides access to the raw data for a document as a bytes (Py3) or string (Py2)
            # If it's not directly available, it will be converted when we try to retrieve the raw data
            try:
                data = doc.raw_data
            except AttributeError:
                # Instead of type-checking every document, we assume that if it has a raw_data attr, this
                # is the right thing to use
                # If a bytes object is given, we assume that's the doc's raw data
                if isinstance(doc, bytes):
                    data = doc
                elif not isinstance(doc, DataPointType.Document):
                    # If not, we kick up a fuss, as we've presumably been given something that's not a valid document
                    raise TypeError("documents added to a grouped corpus should be instances of the data point type's "
                                    "document class. Data point type is {}. Got {}".format(
                        self.datatype.data_point_type.name, type(doc).__name__
                    ))
                else:
                    # Some other problem caused this
                    raise
            else:
                # If we got the raw data from a document object, we should also retrieve the metadata from there
                # This can be None
                doc_metadata = doc.metadata or {}
                # If metadata is also given as a kwarg, override with those values
                if metadata is not None:
                    doc_metadata.update(metadata)
                metadata = doc_metadata

            if data is None:
                # For an empty result, signified by None, output an empty file
                data = bytes()

            # TODO In the future, remove this explicit type check
            if not isinstance(data, bytes):
                warnings.warn("document raw data should be provided as a bytes() object. Document type {} got "
                              "a {} instead. This is probably a result of the Python 2-3 conversion".format(
                    self.datatype.data_point_type.name, type(data).__name__,
                ))
            try:
                # This should already be a bytes object, but we do this here
                # to make it more likely that old code works, while the above message is showing and
                data = bytes(data)
            except Exception as e:
                # It's here now to ease the transition to Python 3, as this is going to be a tricky point to get right
                # Check that the data is a unicode string, as expected
                raise TypeError("tried to add a document of type {}, but its raw_data was of type {}, not "
                                "something compatible with bytes(). "
                                "This is probably a result of the Python 2-3 conversion. (Error: {})".format(
                    self.datatype.data_point_type.name, type(data).__name__, e
                ))

            if archive_name != self.current_archive_name:
                # Starting a new archive
                if self.current_archive is not None:
                    # Close the old one
                    self.current_archive.close()
                self.current_archive_name = archive_name
                arc_filename = os.path.join(self.data_dir, "{}.prc".format(archive_name))
                # If we're appending a corpus and the archive already exists, append to it
                self.current_archive = PimarcWriter(arc_filename,
                                                    mode="a" if self.append and os.path.exists(arc_filename) else "w")

            # Add a new document to archive
            if self.gzip:
                # We used to just use zlib to compress, which works fine, but it's not easy to open the files manually
                # Using gzip (i.e. writing gzip headers) makes it easier to use the data outside Pimlico
                gzip_io = StringIO()
                with gzip.GzipFile(mode="wb", compresslevel=9, fileobj=gzip_io) as gzip_file:
                    gzip_file.write(data)
                data = gzip_io.getvalue()
                filename = "{}.gz".format(doc_name)
            else:
                filename = doc_name

            # Append this document's data to the Pimarc
            self.current_archive.write_file(data, name=filename, metadata=metadata)
            self.flush()

            # Keep a count of how many we've added so we can write metadata
            self.doc_count += 1

        def flush(self):
            """ Flush disk write of the archive currently being written. Called after adding a new file """
            if self.current_archive is not None:
                self.current_archive.flush()

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.current_archive is not None:
                self.current_archive.close()
            self.metadata["length"] = self.doc_count
            super(GroupedCorpus.Writer, self).__exit__(exc_type, exc_val, exc_tb)

        def _count_written_docs(self):
            """
            Emulates what a reader does to iterate over docs, in order to count up how many
            docs have already been written. Used when appending an existing corpus and not
            trusting the stored length in the metadata.

            """
            # Look for already written archives
            archive_filenames = GroupedCorpus.Reader.Setup._get_archive_filenames(self.data_dir)
            archive_filenames.sort()

            total_docs = 0
            for archive_filename in archive_filenames:
                # Count the docs in each archive
                with PimarcReader(archive_filename) as arc:
                    total_docs += len(arc)
            return total_docs


def exclude_invalid(doc_iter):
    """
    Generator that skips any invalid docs when iterating over a document dataset.

    """
    return ((doc_name, doc) for (doc_name, doc) in doc_iter if not is_invalid_doc(doc))


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
        for corpus_items in zip(
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


class GroupedCorpusWithTypeFromInput(DynamicOutputDatatype):
    """
    Dynamic datatype that produces a GroupedCorpus with a document datatype that is the same as the input's
    document/data-point type.

    If the input name is not given, uses the first input.

    Unlike :class:`CorpusWithTypeFromInput`, this does not infer whether the result should be
    a grouped corpus or not: it always is. The input should be an iterable corpus (or subtype,
    including grouped corpus), and that's where the datatype will come from.

    """
    datatype_name = "grouped corpus with input doc type"

    def __init__(self, input_name=None):
        self.input_name = input_name

    def get_base_datatype(self):
        return GroupedCorpus()

    def get_datatype(self, module_info):
        from pimlico.core.modules.base import satisfies_typecheck, TypeCheckError

        input_datatypes = module_info.get_input_datatype(self.input_name, always_list=True)
        if not satisfies_typecheck(input_datatypes[0], IterableCorpus()):
            raise TypeCheckError("tried to get data point type from input {} to module {}, but input "
                                 "is not an iterable corpus (it's a {})".format(
                self.input_name or "(default)", module_info.module_name, input_datatypes[0]))
        # Get the document type from the input iterable corpus
        input_document_type = module_info.get_input_datatype(self.input_name, always_list=True)[0].data_point_type
        return GroupedCorpus(input_document_type)


class CorpusWithTypeFromInput(DynamicOutputDatatype):
    """
    Infer output corpus' data-point type from the type of an input. Passes the data point type through.
    Similar to :class:`GroupedCorpusWithTypeFromInput`, but more flexible.

    If the input is a grouped corpus, so is the output. Otherwise, it's just an IterableCorpus.

    Handles the case where the input is a multiple input. Tries to find a
    common data point type among the inputs.
    They must have the same data point type, or all must be subtypes of one of them.
    (In theory, we could find the most specific common ancestor and use that as the output type,
    but this is not currently implemented and is probably not worth the trouble.)

    Input name may be given. Otherwise, the default input is used.

    """
    datatype_name = "corpus with data-point from input"

    def __init__(self, input_name=None):
        self.input_name = input_name

    def get_datatype(self, module_info):
        datatypes = module_info.get_input_datatype(self.input_name, always_list=True)
        dp_types = [t.data_point_type for t in datatypes]

        # Find the common data point type to use for the output
        # Simplest case: all identical
        if all(t is dp_types[0] for t in dp_types[1:]):
            dp_type = dp_types[0]
        else:
            # Otherwise, check for each one whether all the others are subtypes
            for dpt in dp_types:
                if all(isinstance(t1, type(dpt)) for t1 in dp_types):
                    dp_type = dpt
                    break
            else:
                # No type to serve as the common type
                raise TypeError(
                    "incompatible data point types for concatenation: %s" % ", ".join(t.__name__ for t in dp_types))

        # Check whether the inputs are all grouped corpora
        if all(isinstance(datatype, GroupedCorpus) for datatype in datatypes):
            return GroupedCorpus(dp_type)
        else:
            # If they're not all grouped corpora, just produce an iterable corpus
            return IterableCorpus(dp_type)


class CorpusAlignmentError(Exception):
    pass


class GroupedCorpusIterationError(Exception):
    pass
