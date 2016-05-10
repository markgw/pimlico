from StringIO import StringIO

from pimlico.datatypes.tar import TarredCorpusWriter, pass_up_invalid, TarredCorpus


__all__ = ["CandcOutputCorpus", "CandcOutputCorpusWriter"]


class CandcOutputCorpus(TarredCorpus):
    datatype_name = "candc_output"

    def process_document(self, data):
        data = super(CandcOutputCorpus, self).process_document(data)
        return CandcOutput(data)


class CandcOutputCorpusWriter(TarredCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Data should be a CandcOutput
        return doc.raw_data


class CandcOutput(object):
    """
    C&C output is kept as raw text, since we just want to store it as it comes out from the parser.
    We only pull it apart when it's needed.

    """
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self._sentences = None

    def __iter__(self):
        return iter(self.sentences)

    def iter_sentences(self):
        # Remove the comments, plus the next line (which is empty) from the beginning of the file
        s = iter(StringIO(self.raw_data))
        for l in s:
            if not l.startswith("#"):
                break
        data = "".join(s)
        # Now the rest is sentences, separated by blank lines
        for sentence_data in data.split("\n\n"):
            sentence_data = sentence_data.strip("\n ")
            if sentence_data:
                # Wrap each sentence up in an object that helps us pull it apart
                yield CandcSentence(sentence_data)

    @property
    def sentences(self):
        if self._sentences is None:
            self._sentences = list(self.iter_sentences())
        return self._sentences

    def __getitem__(self, item):
        return self.sentences[item]


class CandcSentence(object):
    def __init__(self, data):
        self.data = data
        self._tag_dicts = None
        self._grs = None

    def split_grs_and_tag_line(self):
        # Should be the last line of the data and start with <c>
        grs,__, tag_line = self.data.rpartition("\n")
        if tag_line.startswith("<c>"):
            # GRs may be empty
            return grs if grs.strip("\n ") else None, tag_line
        else:
            # Seems to be no tag line
            return self.data, None

    @property
    def tag_dicts(self):
        if self._tag_dicts is None:
            tag_line = self.tag_line
            if tag_line is None:
                return None
            else:
                tags = [tag.split("|") for tag in tag_line[4:].strip().split(" ")]
                self._tag_dicts = [
                    {
                        "word": tag[0], "lemma": tag[1], "pos": tag[2], "chunk": tag[3], "ne": tag[4], "supertag": tag[5]
                    } for tag in tags
                ]
        return self._tag_dicts

    @property
    def tag_line(self):
        return self.split_grs_and_tag_line()[1]

    @property
    def grs(self):
        if self._grs is None:
            gr_text = self.split_grs_and_tag_line()[0]
            if gr_text is None:
                self._grs = GrammaticalRelations([])
            else:
                self._grs = GrammaticalRelations.from_string(gr_text)
        return self._grs


class GrammaticalRelation(object):
    """ A grammatical relation (Briscoe and Caroll) in set as output by C&C. """
    def __init__(self, dep_type, args):
        # String dependency type
        self.dep_type = dep_type
        # List of word indices
        self.args = args

    def __str__(self):
        return "(%s, %s)" % (self.dep_type,
                             ", ".join("%s%s" % (word, "_%d" % index if index is not None else "")
                                       for (word, index) in self.args))

    def __repr__(self):
        return str(self)

    @staticmethod
    def _split_lex(s):
        if s == "_":
            return None, None
        word, __, index = s.rpartition("_")

        if not word:
            # This is a non-word marker, e.g. poss or obj
            word = index
            index = None
        else:
            index = int(index)
        return word, index

    @staticmethod
    def from_string(line):
        """
        Parse a GR from a single line of text
        """
        tokens = line.strip("()\n ").split()
        dep_type = tokens[0]
        args = [GrammaticalRelation._split_lex(t) for t in tokens[1:]]
        return GrammaticalRelation(dep_type, args)


class GrammaticalRelations(object):
    """
    A graph (set) of grammatical relations, which are somewhat richer than dependencies. Represents the full
    GR output for a sentence from C&C.

    """
    def __init__(self, grs):
        # List of GRs (see above)
        self.grs = grs
        # Build the word map
        self.words = {}
        for dep in self.grs:
            for word, index in dep.args:
                if word is not None and index is not None:
                    self.words[index] = word

    @staticmethod
    def from_string(string):
        """
        Build a single dependency graph from a string.

        """
        # Normal dependencies look like:
        #  (type word0_id0 word1_id1 [word2_id2])
        # Ignore any blank lines
        return GrammaticalRelations([GrammaticalRelation.from_string(line) for line in string.splitlines() if line])

    def get_by_arg0(self, word):
        return [dep for dep in self.grs if len(dep.args) > 0 and dep.args[0][1] == word]

    def get_by_arg1(self, word):
        return [dep for dep in self.grs if len(dep.args) > 1 and dep.args[1][1] == word]

    def get_outgoing_edges(self):
        """
        Builds something more like an actual graph data structure from the arc-only representation of
        the graph used by default.

        """
        word_edges = {}
        for dependency in self.grs:
            # The source of the edge is the first argument
            source_word = dependency.args[0][1]
            for arg_num, (__, dest_word) in enumerate(dependency.args[1:]):
                # Add an edge from the source word to each other arg
                word_edges.setdefault(source_word, []).append(((dependency.dep_type, arg_num), dest_word))
        return word_edges

    def build_incoming_edges(self):
        """
        The upward version of build_outgoing_edges().

        """
        word_edges = {}
        for dependency in self.grs:
            # The source of the edge is the first argument
            source_word = dependency.args[0][1]
            for arg_num, (__, dest_word) in enumerate(dependency.args[1:]):
                # Add an edge from the source word to each other arg, indexed upwards
                word_edges.setdefault(dest_word, []).append(((dependency.dep_type, arg_num), source_word))
        return word_edges
