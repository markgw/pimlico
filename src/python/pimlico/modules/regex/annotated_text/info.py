import re

from pimlico.core.modules.base import ModuleInfoLoadError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.features import KeyValueListCorpus, KeyValueListCorpusWriter
from pimlico.datatypes.tar import TarredCorpus
from pimlico.datatypes.word_annotations import WordAnnotationCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "annotated_text_matcher"
    module_inputs = [("documents", WordAnnotationCorpus)]
    module_outputs = [("documents", KeyValueListCorpus)]
    module_options = {
        "expr": {
            "help": "An expression to determine what to search for in sentences. Consists of a sequence of tokens, "
                    "each matching one field in the corresponding token's annotations in the data. These are "
                    "specified in the form field[x], where field is the name of a field supplied by the input "
                    "data and x is the value required of that field. If x ends in a *, it will match prefixes: "
                    "e.g. pos[NN*]. If no field name is given, the default 'word' is used. "
                    "A token of the form 'x=y' matches the expression y as above and assigns the matching word to "
                    "the extracted variable x (to be output). You may also extract a different annotation field by "
                    "specifying x=f:y, where f is the field name to be extracted. "
                    "E.g. 'what a=lemma:pos[NN*] lemma[come] with b=pos[NN*]' matches phrases like 'what meals come "
                    "with fries', producing 'a=meal' and 'b=fries'. Both pos and lemma need to be fields in the "
                    "dataset'",
            "required": True,
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)

        # Break down the expression, but don't yet produce a regex, since we don't necessarily know what fields
        #  are available or where they are in the input
        self.deconstructed_expression = deconstruct_expression(self.options["expr"])
        self.required_fields = set(
            sum(([x[0], x[4]] for x in self.deconstructed_expression), [])
        ) - {None}

        input_datatype = self.get_input_datatype()[1]

        if input_datatype.annotation_fields is not None:
            # The annotation subclass tells us what fields it has available
            # We can check that all the fields mentioned in the expression are available
            # Otherwise, this check has to wait until runtime, when we can instantiate the datatype
            unknown_fields = self.required_fields - set(input_datatype.annotation_fields)
            if unknown_fields:
                raise ModuleInfoLoadError(
                    "matching expression uses fields (%s) not supplied by the input datatype. Input supplies: %s" % (
                        ", ".join("'%s'" % f for f in unknown_fields), ", ".join(input_datatype.annotation_fields)
                    )
                )
        if not any(x[3] is not None and x[4] is not None for x in self.deconstructed_expression):
            raise ModuleInfoLoadError("expression '%s' does not include any variable extractions, so no data would "
                                      "be output by running this" % self.options["expr"])

    def get_writer(self, output_name, append=False):
        base_dir = self.get_output_dir(output_name)
        if output_name == "documents":
            return KeyValueListCorpusWriter(base_dir, append=append)


def deconstruct_expression(expression):
    """
    Pull an expression apart. This is used to check that an expression is syntactically
    correct and also to parse it into a regex (which is only done at execution time).

    :param expression: expr option from the config
    :return:
    """
    split_tokens = []
    for token in expression.split():
        extract_field_name = None
        var_name = None

        if "=" in token:
            # This is a variable assignment
            var_name, __, token = token.partition("=")
            # Expression may start with a field name specifier
            if ":" in token:
                extract_field_name, __, token = token.partition(":")
            else:
                # Default field name to extract
                extract_field_name = "word"

        # Rest of the token is a matching expression
        if "[" in token:
            # Specifies field name to match
            match_field_name, __, token = token.partition("[")
            # Remove the closing ]
            token = token[:-1]
        else:
            # By default, match the 'word' field
            match_field_name = "word"

        # Check if it's a prefix
        if token.endswith("*"):
            prefix = True
            token = token[:-1]
        else:
            prefix = False

        split_tokens.append((match_field_name, token, prefix, var_name, extract_field_name))
    return split_tokens
