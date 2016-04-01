import os
import re
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self):
        # Turn off document processing on the input iterator
        # This means we'll just get raw text for each document
        self.input_corpora[0].raw_input = True

        # Now we're able to check what fields will actually be returned by the input datatype
        # Check we've got all the ones used by the expression
        available_fields = self.input_corpora[0].read_annotation_fields()
        unknown_fields = self.info.required_fields - set(available_fields)
        if unknown_fields:
            if self.input_corpora[0].annotation_fields is None:
                extra_mess = ". This would not have been caught by pre-execution checks, since the input datatype's " \
                             "metadata does not declare what fields it supplies"
            elif set(self.input_corpora[0].annotation_fields) == set(available_fields):
                # Datatype reported having this set of fields, so this wouldn't have passed the config checks
                extra_mess = ""
            else:
                extra_mess = ". (Datatype reports having a different set of fields: %s)" % \
                             ", ".join(self.input_corpora[0].annotation_fields)

            raise ModuleExecutionError(
                "matching expression uses fields (%s) not supplied by the input datatype. Input supplies: %s%s" % (
                    ", ".join("'%s'" % f for f in unknown_fields), ", ".join(available_fields), extra_mess
                ))

        self.word_boundary = self.input_corpora[0].metadata["word_boundary"].replace("\\n", "\n")

        # Process the expression into a regex that we'll match against the text
        regex_words = []
        word_format = self.input_corpora[0].metadata["word_format"].replace("\\n", "\n")
        nonwords = self.input_corpora[0].metadata["nonword_chars"].replace("\\n", "\n")
        self.capture_fields = []

        for word_num, (match_field_name, target, prefix, var_name, extract_field_name) \
                in enumerate(self.info.deconstructed_expression):
            # Build a regex component that matches the required field to the target value
            if prefix:
                # Allow more chars after the target
                target = r"%s.*?" % target
            regex_words.append(build_re(word_format, match_field_name, target, "%d" % word_num, nonwords))

            if var_name is not None and extract_field_name is not None:
                # A particular field of this word will be extracted to go in the output
                self.capture_fields.append((var_name, "%s%s" % (extract_field_name, word_num)))

        regex = "%s%s%s" % (self.word_boundary, self.word_boundary.join(regex_words), self.word_boundary)

        try:
            self.regex = re.compile(regex)
        except Exception, e:
            raise ModuleExecutionError("could not compile regex: %s. %s" % (regex, e))
        self.log.info("Matching regex %s" % regex.replace("\n", "\\n"))

        self.match_count = 0
        self.matched_docs = []

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Add word boundaries either side of the doc text so we match at the beginning and end
        doc = "%s%s%s" % (self.word_boundary, doc, self.word_boundary)
        # Search using the pre-prepared regex
        output_lines = []
        matched = 0
        for match in self.regex.finditer(doc):
            matched += 1
            # For each match of the regex, add a line to the output document
            match_dict = match.groupdict()
            output_lines.append(" ".join("%s=%s" % (var, match_dict[group]) for (var, group) in self.capture_fields))

        self.match_count += matched
        if matched:
            self.matched_docs.append((archive, filename))
        return "\n".join(output_lines)

    def postprocess(self, error=False):
        self.log.info("Regex matched a total of %d times in %d documents" % (self.match_count, len(self.matched_docs)))
        match_filename = os.path.join(self.info.get_output_dir("documents"), "matched_docs.txt")
        self.log.info("Outputing matched doc list to %s" % match_filename)
        # Output a list of the non-empty files
        with open(match_filename, "w") as f:
            f.write("\n".join("%s/%s" % (archive, filename) for (archive, filename) in self.matched_docs))


def build_re(word_format, match_field, match_expr, group_suffix, nonwords):
    # First escape the whole thing in case it uses characters that have a special meaning in a regex
    word_format = re.escape(word_format)
    # The word format includes field specifiers of the form {name}
    # Look for the particular field we want to match and put the matching expression in the regex for it
    word_format = re.sub(r"\\{%s\\}" % match_field,
                         "(?P<%s%s>%s)" % (match_field, group_suffix, match_expr),
                         word_format)
    # Replace all other fields to make a regex with a named group by which they'll be captured
    word_format = re.sub(r"\\{(.+?)\\}", r"(?P<\g<1>%s>[^%s]*)" % (group_suffix, nonwords), word_format)
    return word_format
