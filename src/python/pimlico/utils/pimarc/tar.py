"""
Wrapper around tar reader, to provide the same interface as Pimarc.

This means we can deprecate the use of tar files, but keep backwards compatibility
for a time, whilst moving over to direct use of Pimarc objects.

"""
from builtins import bytes
from future.utils import PY2

import os
import shutil
import tarfile
from tempfile import mkdtemp

from itertools import islice

from pimlico.utils.pimarc.reader import StartAfterFilenameNotFound


class PimarcTarBackend(object):
    def __init__(self, archive_filename):
        self.archive_filename = archive_filename
        self.archive_file = None
        self.closed = False

    def open(self):
        self.archive_file = tarfile.open(self.archive_filename, mode="r:")
        return self.archive_file

    def close(self):
        self.archive_file.close()
        self.closed = True

    def __enter__(self):
        self.archive_file = self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_metadata(self, filename):
        """
        Metadata is always the same with the tar backend: just a dictionary containing
        the key `name` with the filename.

        """
        return {"name": filename}

    def __getitem__(self, item):
        """
        Random access into the archive. Load a named file's data and metadata.

        This is a very bad thing to do (at least to do many times) with tar files. That's
        why I've replaced tar files with Pimarc. However, for backwards compatibility,
        we do this in the inefficient way the tar allows.

        """
        return self._get_metadata(item), self.archive_file.extractfile(item).read()

    def iter_filenames(self):
        """
        Just iterate over the filenames (decoded if necessary). Used to create metadata,
        check for file existence, etc.

        Not as fast as with Pimarc, as we need to pass over the whole archive file to
        read all the names.

        """
        # Make sure we're at the start of the file
        self.archive_file.fileobj.seek(0)
        for tarinfo in self.archive_file:
            if PY2:
                yield tarinfo.name.decode("utf-8")
            else:
                yield tarinfo.name

    def iter_metadata(self):
        """
        Iterate over all files in the archive, yielding just the metadata, skipping
        over the data.

        """
        for filename in self.iter_filenames():
            yield self._get_metadata(filename)

    def iter_files(self, skip=None, start_after=None):
        """
        Iterate over files, together with their JSON metadata, which includes their name (as "name").

        :param start_after: skips all files before that with the given name, which is
            expected to be in the archive
        :param skip: skips over the first portion of the archive, until this number of documents have
            been seen. Ignored is start_after is given.
        """
        # Make sure we're at the start of the file
        self.archive_file.fileobj.seek(0)

        # Prepare a temporary directory to extract everything to
        tmp_dir = mkdtemp()

        started = True
        tarinfo_iter = self.archive_file
        if start_after is not None:
            # Don't start until we encounter the filename
            started = False
        elif skip is not None:
            # Skip over the given number of files
            tarinfo_iter = islice(self.archive_file, skip, None)

        try:
            for tarinfo in tarinfo_iter:
                if PY2:
                    filename = tarinfo.name.decode("utf-8")
                else:
                    filename = tarinfo.name

                if not started:
                    # Check whether this is the file we're to start after
                    if filename == start_after:
                        # Skip this file, but start on the next one
                        started = True
                    continue

                # Extract the raw file data
                self.archive_file.extract(tarinfo, tmp_dir)
                # Read in the data
                with open(os.path.join(tmp_dir, filename), "rb") as f:
                    raw_data = f.read()

                # Wrap in bytes
                # In Py2, this converts the string to a bytes backport
                # In Py3, this is a no-op
                raw_data = bytes(raw_data)

                yield self._get_metadata(filename), raw_data

                # Remove the file once we're done with it (when we request another)
                os.remove(os.path.join(tmp_dir, filename))
        finally:
            # Remove the temp dir
            shutil.rmtree(tmp_dir)

        # Catch the case where the filename requested as a starting point wasn't found
        if not started and start_after is not None:
            raise StartAfterFilenameNotFound("filename '{}' not found in the tar archive".format(start_after))

    def __iter__(self):
        return self.iter_files()

    def __len__(self):
        self.archive_file.fileobj.seek(0)
        return sum((1 for tarinfo in self.archive_file), 0)
