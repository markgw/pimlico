from pimlico.core.modules.map import DocumentMapModuleExecutor


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self, info):
        # Turn off document processing on the input iterator
        # This means we'll just get raw text for each document
        self.input_corpora[0].raw_input = True
        self.regex = info.regex
        self.log.info("Matching regex %s" % self.regex.pattern)
        self.match_count = 0
        self.matched_docs = 0

    def process_document(self, filename, doc):
        # Add spaces either side of the doc text so we match at the beginning and end
        doc = " %s " % doc
        # Search using the pre-prepared regex
        output_lines = []
        matched = 0
        for match in self.regex.finditer(doc):
            matched += 1
            # For each match of the regex, add a line to the output document
            output_lines.append(" ".join("%s=%s" % (var, val) for (var, val) in match.groupdict().items()))

        self.match_count += matched
        if matched:
            self.matched_docs += 1
        return "\n".join(output_lines)

    def postprocess(self, info, error=False):
        self.log.info("Regex matched a total of %d times in %d documents" % (self.match_count, self.matched_docs))
