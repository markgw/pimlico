import json

from builtins import super, bytes

from .utils import _read_var_length_data, _skip_var_length_data
from .index import PimarcIndex


class PimarcReader(object):
    """
    The Pimlico Archive format: read-only archive.

    """
    def __init__(self, archive_filename):
        self.archive_filename = archive_filename
        if not archive_filename.endswith(".prc"):
            raise IOError("pimarc files should have the extension '.prc'")
        self.index_filename = "{}i".format(archive_filename)

        self.archive_file = open(self.archive_filename, mode="rb")
        self.index = PimarcIndex.load(self.index_filename)
        self.closed = False

    def close(self):
        self.archive_file.close()
        # Allow garbage collection of the index
        self.index = None
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getitem__(self, item):
        """
        Random access into the archive. Load a named file's data and metadata.

        """
        # Look up the filename in the index and get pointers to its metadata and data
        metadata_start, data_start = self.index[item]
        # Jump to the start of the metadata
        self.archive_file.seek(metadata_start)
        # Read the metadata
        metadata = self._read_metadata()
        # There's some redundancy in this case: we're now presumably at the start
        # of the data, so don't need data_start
        # Assume that this is the case and continue reading from where we stopped
        data = _read_var_length_data(self.archive_file)
        return metadata, data

    def read_file(self, filename):
        """ Load a file. Same as `reader[filename]` """
        return self[filename]

    def iter_filenames(self):
        """
        Iterate over just the filenames in the archive, without further metadata or file data.
        Fast for Pimarc, as the index is fully loaded into memory.

        """
        return iter(self.index.keys())

    def _read_metadata(self):
        """
        Assuming the file is currently at the start of a metadata block, read and
        parse that metadata.

        """
        # Read the metadata
        return PimarcFileMetadata(_read_var_length_data(self.archive_file))

    def _skip_block(self):
        """
        Assuming the file is currently at the start of a metadata block or a file block,
        read how long it is and skip over it.

        """
        _skip_var_length_data(self.archive_file)

    def iter_metadata(self):
        """
        Iterate over all files in the archive, yielding just the metadata, skipping
        over the data.

        """
        # Make sure we're at the start of the file
        self.archive_file.seek(0)
        while True:
            # Try reading the metadata of the next file
            try:
                metadata = self._read_metadata()
            except EOFError:
                # At this point, it's normal to get an EOF: we've just got to the end neatly
                break
            # This should be followed by the file's data, which we skip over, since we don't need it
            self._skip_block()
            yield metadata

    def iter_files(self, skip=None, start_after=None):
        """
        Iterate over files, together with their JSON metadata, which includes their name (as "name").

        :param start_after: skips all files before that with the given name, which is
            expected to be in the archive
        :param skip: skips over the first portion of the archive, until this number of documents have
            been seen. Ignored is start_after is given.
        """
        if start_after is not None:
            # Look up this filename in the index
            if start_after not in self.index:
                raise StartAfterFilenameNotFound("filename '{}' not found in the Pimarc archive".format(start_after))
            # Get the start byte of the file's data
            start_after_start_byte = self.index.get_data_start_byte()
            # Seek to this byte, then skip over the data, so we're at the start of the next file's metadata
            self.archive_file.seek(start_after_start_byte)
            self._skip_block()
            # Don't skip any more files
            started = True
        else:
            # Make sure we're at the start of the file
            self.archive_file.seek(0)

            if skip is not None and skip < 1:
                skip = None
            # Don't wait to start if skip is not given
            started = skip is None

        skipped = 0
        while True:
            if not started:
                # Skip this file's metadata
                self._skip_block()
                # And the file's data
                self._skip_block()

                skipped += 1
                if skipped >= skip:
                    # Skipped enough files: start reading at the next one
                    started = True
            else:
                # Try reading the metadata of the next file
                try:
                    metadata = self._read_metadata()
                except EOFError:
                    # At this point, it's normal to get an EOF: we've just got to the end neatly
                    break
                # This should be followed by the file's data immediately
                # Read it in
                # If there's an EOF here, something's wrong with the file
                data = _read_var_length_data(self.archive_file)

                # Wrap in bytes
                # In Py2, this converts the string to a bytes backport
                # In Py3, this is a no-op
                data = bytes(data)

                yield metadata, data

    def __iter__(self):
        return self.iter_files()

    def __len__(self):
        return len(self.index)


def metadata_decode_decorator(fn):
    def _new_fn(self, *args, **kwargs):
        self.decode()
        return fn(self, *args, **kwargs)
    return _new_fn


class PimarcFileMetadata(dict):
    """
    Simple wrapper around the JSON-encoded metadata associated with a file in a
    Pimarc archive. When the metadata is loaded, the raw bytes data is wrapped in
    an instance of PimarcFileMetadata, so that it can be easily decoded when
    needed, but avoiding decoding all metadata, which might not ever be needed.

    You can simply use the object as if it is a dict and it will decode the JSON
    data the first time you try accessing it. You can also call `dict(obj)` to
    get a plain dict instead.

    """
    def __init__(self, raw_data):
        super().__init__()
        self.raw_data = raw_data
        self._decoded = False

    def decode(self):
        if not self._decoded:
            # Decode the metadata and parse as JSON
            self.update(json.loads(self.raw_data.decode("utf-8")))
            self._decoded = True

    __getitem__ = metadata_decode_decorator(dict.__getitem__)
    __setitem__ = metadata_decode_decorator(dict.__setitem__)
    __delitem__ = metadata_decode_decorator(dict.__delitem__)
    keys = metadata_decode_decorator(dict.keys)
    values = metadata_decode_decorator(dict.values)
    items = metadata_decode_decorator(dict.items)


class StartAfterFilenameNotFound(KeyError):
    pass
