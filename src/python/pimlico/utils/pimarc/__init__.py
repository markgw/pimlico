"""The Pimlico Archive format

Implementation of a simple multi-file archive format, somewhat like tar.

Pimlico multi-file datasets currently use tar to store many files in one archive. This
was attractive because of its simplicity and the fact that the files can be iterated
over in order efficiently. However, tar is an old format and has certain quirks.
The biggest downside is that random access (reading files not in the order stored or
jumping into the middle of an archive) is very slow.

The Pimlico Archive format (prc) aims to be a very simple generic archive format.
It has the same property as tars that it is fast to iterate over files in order. But
it also stores an index that can be loaded into memory to make it quick to jump into
the archive and potentially access the files in a random order.

It stores very little information about the files. In this sense, it is simpler than
tar. It does not store, for example, file timestamps or permissions, since we do not
need these things for documents in a Pimlico corpus. It does, however, have a generic
JSON metadata dictionary for each file, so metadata like this can be stored as
necessary.

Iterating over files in order is still likely to be substantially faster than random
access (depending on the underlying storage), so it is recommended to add files to
the archive in the sequential order that they are used in. This is the typical use
case in Pimlico: a dataset is created in order, one document at a time, and stored
iteratively. Then another module reads and processes those documents in the same order.

In keeping with this typical use case in Pimlico, a Pimarc can be opened for reading
only, writing only (new archive) or appending, just like normal files. You cannot,
for example, open an archive and move files around, or delete a file. To do these
things, you must read in an archive using a reader and write out a new, modified one
using a writer.

Restrictions on filenames:
Filenames may use any unicode characters, excluding EOF, newline and tab.

"""
from .reader import PimarcReader
from .writer import PimarcWriter


def open_archive(path, mode="r"):
    if mode == "r":
        return PimarcReader(path)
    elif mode in ("w", "a"):
        return PimarcWriter(path, mode=mode)
    else:
        raise ValueError("unknown mode '{}'".format(mode))
