# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Input reader for VRT text collections (`VeRticalized Text, as used by Korp:
<https://www.kielipankki.fi/development/korp/corpus-input-format/#VRT_file_format>`_), just for
reading the (tokenized) text content, throwing away all the annotations.

Uses sentence tags to divide each text into sentences.


.. seealso::

   :mod:`pimlico.modules.input.text_annotations.vrt`:
      Reading VRT files with all their annotations

"""

from pimlico.core.modules.inputs import iterable_input_reader_factory
from pimlico.datatypes.tokenized import TokenizedDocumentType
from pimlico.datatypes.vrt import VRTDocumentType
from pimlico.modules.input.text.raw_text_files.info import ModuleInfo as RawTextModuleInfo
from pimlico.modules.input.text_annotations.vrt.info import VRTOutputType


class VRTTextOutputType(VRTOutputType):
    data_point_type = TokenizedDocumentType

    def filter_text(self, doc):
        return [[w.word for w in sent]
                for sent in VRTDocumentType(self.reader_options, {}).process_document(doc).sentences]


ModuleInfo = iterable_input_reader_factory(
    dict(RawTextModuleInfo.module_options, **{
        # More options may be added here
    }),
    VRTTextOutputType,
    module_type_name="vrt_files_reader",
    module_readable_name="VRT annotated text files",
    execute_count=True,
)
