"""
Input reader to fetch a text corpus from Huggingface's datasets library.
See: https://huggingface.co/datasets/.

Uses Huggingface's ``load_dataset()`` function to download a dataset and
then converts it to a Pimlico raw text archive.

"""
from pimlico.core.modules.options import comma_separated_strings

from pimlico.core.dependencies.python import huggingface_datasets_dependency

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "huggingface_text"
    module_readable_name = "Huggingface text corpus"
    module_inputs = []
    module_outputs = [
        ("default", GroupedCorpus(RawTextDocumentType())),
    ]
    module_options = {
        "dataset": {
            "help": "Name of the dataset to download",
            "required": True,
        },
        "name": {
            "help": "Name defining the dataset configuration. This corresponds to the second argument of "
                    "load_dataset()",
        },
        "split": {
            "help": "Restrict to a split of the data. Must be one of the splits that this "
                    "dataset provides. The default value of 'train' will work for many datasets, but is "
                    "not guaranteed to be appropriate",
            "default": "train",
        },
        "columns": {
            "help": "Name(s) of column(s) to store as Pimlico datasets. At least one must be given",
            "required": True,
            "type": comma_separated_strings,
        },
        "doc_name": {
            "help": "Take the doc names from the named column. The special value 'enum' (default) just numbers "
                    "the sequence of documents",
            "default": "enum",
        }
    }

    def provide_further_outputs(self):
        """
        In addition to the default output ``default``, if more than one column is specified,
        further outputs will be provided, each containing a column and named after the column.

        The first column name given is always provided as the first (default) output, called
        "default".

        """
        return [
            (col_name, GroupedCorpus(RawTextDocumentType())) for col_name in self.options["columns"][1:]
        ]

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [huggingface_datasets_dependency]
