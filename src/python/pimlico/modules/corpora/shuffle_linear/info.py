"""
Randomly shuffles all the documents in a grouped corpus, outputting
them to a new set of archives with the same sizes as the input archives.

It is difficult to do this efficiently for a large corpus when we cannot
randomly access the input documents. Under the old, now deprecated,
tar-based storage format, random access was costly. If a corpus is
produced on the fly, e.g. from a filter or input reader, random access
is impossible.

We use a strategy where the input documents are read in linear order
and placed into a temporary set of small archives ("bins"). Then these are
concatenated into the larger archives, shuffling the documents in memory
in each during the process.

The expected average size of the temporary bins can be set using the
``bin_size`` parameter. Alternatively, the exact total number of
bins to use can be set using the ``num_bins`` parameter.

It may be necessary to lower the bin size if, for example, your
individual documents are very large files. You might also find the
process is noticeably faster with a higher bin size if your files
are small.

.. seealso::

   Module type :mod:`pimlico.modules.corpora.shuffle`
      If the input corpus is not dynamically produced and is therefore
      randomly accessible, it is more efficient to use the ``shuffle``
      module type.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpusWithTypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "shuffle"
    module_readable_name = "Random shuffle (linear)"
    module_inputs = [("corpus", GroupedCorpus())]
    module_outputs = [("corpus", GroupedCorpusWithTypeFromInput())]
    module_options = {
        "bin_size": {
            "help": "Target expected size of temporary bins into which documents "
                    "are shuffled. The actual size may vary, but they will on average "
                    "have this size. Default: 100",
            "type": int,
            "default": 100,
        },
        "num_bins": {
            "help": "Directly set the number of temporary bins to put document into. "
                    "If set, bin_size is ignored",
            "type": int,
        },
        "keep_archive_names": {
            "help": "By default, it is assumed that all doc names are unique to the "
                    "whole corpus, so the same doc names are used once the documents "
                    "are put into their new archives. If doc names are only unique "
                    "within the input archives, use this and the input archive names "
                    "will be included in the output document names. Default: False",
            "type": str_to_bool,
            "default": False,
        },
        "archive_basename": {
            "help": "Basename to use for archives in the output corpus. Default: 'archive'",
            "default": "archive",
        },
    }
    module_supports_python2 = True
