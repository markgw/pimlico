# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import ctypes
import multiprocessing
import os
import re
from multiprocessing import Value

from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


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


def preprocess(executor):
    # Turn off document processing on the input iterator
    # This means we'll just get raw text for each document
    executor.input_corpora[0].raw_data = True

    # Now we're able to check what fields will actually be returned by the input datatype
    # Check we've got all the ones used by the expression
    available_fields = executor.input_corpora[0].read_annotation_fields()
    unknown_fields = executor.info.required_fields - set(available_fields)
    if unknown_fields:
        if executor.input_corpora[0].annotation_fields is None:
            extra_mess = ". This would not have been caught by pre-execution checks, since the input datatype's " \
                         "metadata does not declare what fields it supplies"
        elif set(executor.input_corpora[0].annotation_fields) == set(available_fields):
            # Datatype reported having this set of fields, so this wouldn't have passed the config checks
            extra_mess = ""
        else:
            extra_mess = ". (Datatype reports having a different set of fields: %s)" % \
                         ", ".join(executor.input_corpora[0].annotation_fields)

        raise ModuleExecutionError(
            "matching expression uses fields (%s) not supplied by the input datatype. Input supplies: %s%s" % (
                ", ".join("'%s'" % f for f in unknown_fields), ", ".join(available_fields), extra_mess
            ))

    executor.word_boundary = executor.input_corpora[0].metadata["word_boundary"].replace("\\n", "\n")

    # Process the expression into a regex that we'll match against the text
    word_format = executor.input_corpora[0].metadata["word_format"].replace("\\n", "\n")
    nonwords = executor.input_corpora[0].metadata["nonword_chars"].replace("\\n", "\n")
    executor.capture_fields = []

    executor.regexes = []
    word_num = -1
    for deconstructed_expression in executor.info.deconstructed_expressions:
        regex_words = []
        regex_fields = []
        for word_num, (match_field_name, target, prefix, var_name, extract_field_name) \
                in enumerate(deconstructed_expression, start=word_num+1):
            # Build a regex component that matches the required field to the target value
            if prefix:
                # Allow more chars after the target
                target = r"%s[^%s]*?" % (target, nonwords)
            regex_words.append(build_re(word_format, match_field_name, target, "%d" % word_num, nonwords))

            if var_name is not None and extract_field_name is not None:
                # A particular field of this word will be extracted to go in the output
                regex_fields.append((var_name, "%s%s" % (extract_field_name, word_num)))

        regex = "%s%s%s" % (executor.word_boundary, executor.word_boundary.join(regex_words), executor.word_boundary)
        executor.capture_fields.append(regex_fields)

        try:
            executor.regexes.append(re.compile(regex))
        except Exception as e:
            raise ModuleExecutionError("could not compile regex: %s. %s" % (regex, e))

    for regex in executor.regexes:
        executor.log.info("Matching regex %s" % regex.pattern.replace("\n", "\\n"))

    executor.match_count = Value(ctypes.c_long)
    executor.match_count.value = 0
    executor.matched_docs = multiprocessing.Queue()


@skip_invalid
def process_document(worker, archive, filename, doc):
    executor = worker.executor
    # Add word boundaries either side of the doc text so we match at the beginning and end
    doc = "%s%s%s" % (executor.word_boundary, doc, executor.word_boundary)
    matched = 0
    output_lines = []

    for regex, capture_fields in zip(executor.regexes, executor.capture_fields):
        # Search using the pre-prepared regex
        for match in regex.finditer(doc):
            matched += 1
            # For each match of the regex, add a line to the output document
            match_dict = match.groupdict()
            output_lines.append([(var, match_dict[group]) for (var, group) in capture_fields])

    with executor.match_count.get_lock():
        executor.match_count.value += matched
    if matched:
        executor.matched_docs.put((archive, filename))
    return output_lines


def postprocess(executor, error=False):
    match_count = executor.match_count.value
    matched_docs = []
    while not executor.matched_docs.empty():
        matched_docs.append(executor.matched_docs.get_nowait())
    executor.log.info("Regex matched a total of %d times in %d documents" % (match_count, len(matched_docs)))

    if not error:
        match_filename = os.path.join(executor.info.get_absolute_output_dir("documents"), "matched_docs.txt")
        executor.log.info("Outputing matched doc list to %s" % match_filename)
        # Output a list of the non-empty files
        with open(match_filename, "w") as f:
            f.write("\n".join("%s/%s" % (archive, filename) for (archive, filename) in matched_docs))


ModuleExecutor = multiprocessing_executor_factory(process_document, preprocess_fn=preprocess, postprocess_fn=postprocess)
