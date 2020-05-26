"""
Randomly shuffles all the documents in a grouped corpus, outputting
them to a new set of archives with the same sizes as the input archives.

This was difficult to do this efficiently for a large corpus using the
old tar storage format. There therefore used to be a strategy implemented
here where the input documents were read in linear order
and placed into a temporary set of small archives ("bins") and these were
concatenated into the larger archives, shuffling the documents in memory
in each during the process.

It is no longer necessary to do this, since the standard pipeline-internal
storage format permits efficient random access. However, it may sometimes
be necessary to use the linear-reading strategy: for example, if the input
comes from a filter module, its documents cannot be randomly accessed.

.. todo::

   Currently, this accepts any GroupedCorpus as input, but checks at runtime
   that the input is stored used the pipeline-internal format. It would be
   much better if this check could be enforced at the level of datatypes, so
   that the input datatype requirement explicitly rules out grouped corpora
   coming from input readers, filters or other dynamic sources.

   Since this requires some tricky changes to the datatype system, I'm not
   implementing it now, but it should be done in future.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpusWithTypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "shuffle"
    module_readable_name = "Random shuffle"
    module_inputs = [("corpus", GroupedCorpus())]
    module_outputs = [("corpus", GroupedCorpusWithTypeFromInput())]
    module_options = {
        "archive_basename": {
            "help": "Basename to use for archives in the output corpus. Default: 'archive'",
            "default": "archive",
        },
        "seed": {
            "help": "Seed for the random number generator. "
                    "The RNG is always seeded, for reproducibility. Default: 999",
            "default": 999,
            "type": int,
        },
    }
