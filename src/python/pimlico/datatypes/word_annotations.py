import re

from operator import itemgetter

from pimlico.datatypes.base import DatatypeLoadError, DynamicOutputDatatype, DynamicInputDatatypeRequirement
from pimlico.datatypes.tokenized import TokenizedCorpus
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class WordAnnotationCorpus(TarredCorpus):
    datatype_name = "word_annotations"
    # Subclasses may provide a list of the fields included for each word
    # Doing so allows an extra level of type checking, since datatype users know before the dataset is available
    #  which fields will be in it
    annotation_fields = None

    def __init__(self, base_dir, pipeline):
        super(WordAnnotationCorpus, self).__init__(base_dir, pipeline)
        self._sentence_boundary_re = None
        self._word_re = None
        self._word_boundary = None

    def read_annotation_fields(self):
        """
        Get the available annotation fields from the dataset's configuration. These are the actual
        fields that will be available in the dictionary produced corresponding to each word.

        """
        # To make sure the fields are in the order in which they're specified, order by matching group number
        return list(map(itemgetter(0), sorted(self.word_re.groupindex.items(), key=itemgetter(1))))

    @property
    def sentence_boundary_re(self):
        if self._sentence_boundary_re is None:
            # Load the annotation format from the metadata
            if "sentence_boundary" not in self.metadata:
                raise DatatypeLoadError(
                    "word annotation corpus does not have a sentence boundary specified in its metadata"
                )
            # Prepare a regex for detecting sentence boundaries
            boundary = self.metadata["sentence_boundary"].replace("\\n", "\n")
            # Interpret the boundary specifier as a regex
            self._sentence_boundary_re = re.compile(re.escape(boundary), re.MULTILINE)
        return self._sentence_boundary_re

    @property
    def word_boundary(self):
        if self._word_boundary is None:
            # Load the annotation format from the metadata
            if "word_boundary" not in self.metadata:
                raise DatatypeLoadError(
                    "word annotation corpus does not have a word boundary specified in its metadata"
                )
            # Allow \n to be used as (or in) the word boundary
            self._word_boundary = self.metadata["word_boundary"].replace("\\n", "\n")
        return self._word_boundary

    @property
    def word_re(self):
        if self._word_re is None:
            # Load the annotation format from the metadata
            if "word_format" not in self.metadata:
                raise DatatypeLoadError(
                    "word annotation corpus does not have a word format specified in its metadata"
                )
            if "nonword_chars" not in self.metadata:
                raise DatatypeLoadError(
                    "word annotation corpus does not have non-word chars specified in its metadata"
                )
            # Prepare a regex for detecting sentence boundaries
            fmt = self.metadata["word_format"].replace("\\n", "\n")
            # First escape the whole thing so that we can use characters that have a special meaning in a regex
            fmt = re.escape(fmt)
            # The word format includes field specifiers of the form {name}
            # Replace these to make a regex with a named group
            nonwords = self.metadata["nonword_chars"].replace("\\n", "\n")
            word_re = re.sub(r"\\{(.+?)\\}", r"(?P<\1>[^%s]*)" % re.escape(nonwords), fmt)
            # Require the re to match the full string: it will only be called on individual words
            word_re = "%s$" % word_re
            # Compile the resulting re
            self._word_re = re.compile(word_re)
        return self._word_re

    def process_document(self, doc):
        sentences = []
        while len(doc):
            # Find the next sentence boundary
            sb = self.sentence_boundary_re.search(doc)
            if sb is None:
                # No more sentence boundaries, the rest must be a single sentence
                sentence_text = doc
                doc = ""
            else:
                # Process the text up to the next boundary as a sentence
                sentence_text = doc[:sb.start()]
                doc = doc[sb.end():]
            # Split the sentence on word boundaries
            words = sentence_text.split(self.word_boundary)
            # Parse each word
            matches = [self.word_re.match(word) for word in words]
            # Check that all the words matched the word re
            if None in matches:
                raise AnnotationParseError("word did not match regex for word format: %s. Matching using: %s" %
                                           (words[matches.index(None)], self.word_re.pattern))
            word_dicts = [match.groupdict() for match in matches]
            sentences.append(word_dicts)
        return sentences

    def data_ready(self):
        if not super(WordAnnotationCorpus, self).data_ready():
            return False
        # We now know at least that the data dir exists
        # Check the required formats are specified in the metadata
        try:
            self.sentence_boundary_re
            self.word_boundary
            self.word_re
        except DatatypeLoadError:
            return False
        else:
            return True


class WordAnnotationCorpusWriter(TarredCorpusWriter):
    """
    Ensures that the correct metadata is provided for a word annotation corpus. Doesn't take care of
    the formatting of the data: that needs to be done by the writing code, or by a subclass.

    """

    def __init__(self, sentence_boundary, word_boundary, word_format, nonword_chars, base_dir, **kwargs):
        super(WordAnnotationCorpusWriter, self).__init__(base_dir, **kwargs)
        self.metadata["sentence_boundary"] = sentence_boundary.replace("\n", "\\n")
        self.metadata["word_boundary"] = word_boundary.replace("\n", "\\n")
        self.metadata["word_format"] = word_format.replace("\n", "\\n")
        self.metadata["nonword_chars"] = nonword_chars.replace("\n", "\\n")
        self.write_metadata()


class SimpleWordAnnotationCorpusWriter(WordAnnotationCorpusWriter):
    """
    Takes care of writing word annotations in a simple format, where each line contains a sentence, words
    are separated by spaces and a series of annotation fields for each word are separated by |s (or a given
    separator). This corresponds to the standard tag format for C&C.

    """

    def __init__(self, base_dir, field_names, field_sep=u"|", **kwargs):
        self.field_names = field_names
        self.field_sep = field_sep
        # Prepare a word format that includes the given field names
        word_format = field_sep.join(u"{%s}" % field for field in field_names)
        super(SimpleWordAnnotationCorpusWriter, self).__init__(u"\n", u" ", word_format, u" \n%s" % field_sep,
                                                               base_dir, **kwargs)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        """
        Takes data in the form of a list of sentences, where each is a list of words, where each
        is a list of values for each field (in the same order in which the field names were given).
        Encodes it in a format that can be read by a WordAnnotationCorpus.

        :param data: sentence data in the form described above
        """
        return u"\n".join(u" ".join(self.field_sep.join(word_fields) for word_fields in sentence) for sentence in doc)


class AddAnnotationField(DynamicOutputDatatype):
    def __init__(self, input_name, add_fields):
        """
        Dynamic type constructor that can be used in place of a module's output type. When called
        (when the output type is needed), dynamically creates a new type that is a WordAnnotationCorpus
        with the same fields as the named input to the module, with the addition of one or more new ones.
        Only works if the input datatype explicitly declares the fields it makes available.

        :param input_name: input to the module whose fields we extend
        :param add_fields: field or fields to add, string names
        """
        super(AddAnnotationField, self).__init__()
        # Make it easy to add just a single field, the most common case
        self.input_name = input_name

        if isinstance(add_fields, basestring):
            add_fields = [add_fields]
        self.add_fields = add_fields
        self.datatype_doc_info = ":class:WordAnnotationCorpus with %s" % ", ".join(add_fields)

    def get_datatype(self, module_info):
        from pimlico.core.modules.base import ModuleInfoLoadError

        input_datatype = module_info.get_input_datatype(self.input_name)[1]
        # Allow the special case where the input datatype is a tokenized corpus
        # Pretend it's an annotated corpus with no annotations, just words
        if issubclass(input_datatype, TokenizedCorpus):
            base_annotation_fields = ["word"]
            new_datatype_name = "word_annotations_%s" % "+".join(self.add_fields)
        else:
            if not issubclass(input_datatype, WordAnnotationCorpus):
                raise ModuleInfoLoadError("cannot construct a dynamic word annotation corpus type, since input we're "
                                          "extending isn't a word annotation corpus. Input '%s' is a %s" %
                                          (self.input_name, input_datatype.__name__))
            if input_datatype.annotation_fields is None:
                raise ModuleInfoLoadError("cannot construct a word annotation corpus type by adding fields to input '%s', "
                                          "since the input type, %s, doesn't explicitly declare its annotation fields" %
                                          (self.input_name, input_datatype.__name__))
            base_annotation_fields = input_datatype.annotation_fields
            new_datatype_name = "%s+%s" % (input_datatype.datatype_name, "+".join(self.add_fields))

        for field in self.add_fields:
            if field in base_annotation_fields:
                raise ModuleInfoLoadError("trying to add a field '%s' to data that already has a field with "
                                          "that name" % field)

        class ExtendedWordAnnotationCorpus(WordAnnotationCorpus):
            datatype_name = new_datatype_name
            annotation_fields = base_annotation_fields + self.add_fields

        return ExtendedWordAnnotationCorpus

    @classmethod
    def get_base_datatype_class(self):
        return WordAnnotationCorpus


class WordAnnotationCorpusWithFields(DynamicInputDatatypeRequirement):
    """
    Dynamic (functional) type that can be used in place of a module's input type. In typechecking, checks whether the
    input module is a WordAnnotationCorpus (or subtype) and whether its fields include all of those required.

    """
    def __init__(self, required_fields):
        super(WordAnnotationCorpusWithFields, self).__init__()

        # Allow just a single field name to be given
        if isinstance(required_fields, basestring):
            required_fields = [required_fields]

        self.required_fields = required_fields
        # Make useful information available to the documentation builder for the module type
        self.datatype_doc_info = \
            ":class:`WordAnnotationCorpus <pimlico.datatypes.word_annotations.WordAnnotationCorpus>` " \
            "with %s field%s" % (" and ".join(
                "'%s'" % f for f in required_fields), "s" if len(required_fields) > 1 else ""
            )

    def check_type(self, supplied_type):
        if not issubclass(supplied_type, WordAnnotationCorpus):
            return False
        if not all(field in supplied_type.annotation_fields for field in self.required_fields):
            return False
        return True


class AnnotationParseError(Exception):
    pass
