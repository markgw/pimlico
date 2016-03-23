import re
from pimlico.core.modules.base import ModuleInfoLoadError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.tar import TarredCorpus
from pimlico.modules.opennlp.pos.datatypes import PosTaggedCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "pos_text_matcher"
    module_inputs = [("text", PosTaggedCorpus)]
    module_outputs = [("documents", TarredCorpus)]
    module_options = {
        "expr": {
            "help": "An expression to determine what to search for in sentences. Consists of a sequence of tokens, "
                    "each a word or POS tag. Words are lower case (matching is case insensitive), POS "
                    "tags are upper case. A token of the form 'x=TAG' matches the tag TAG and assigns it to a "
                    "variable extracted in the output. POS tags ending with a * match tag prefixes. "
                    "E.g. 'my mything=NN* is very myadj=JJ' will matches phrases like 'my foot is very sore', "
                    "producing 'mything=foot' and 'myadj=sore'",
        },
        "regex": {
            "help": "Instead of matching a regex based on a simple expression given in 'expr', specify a regex "
                    "directly. The regex will be matching against POS tagged text, where each word is followed "
                    "by a POS tag separated by '|' and words are separated by spaces. Use named groups to specify "
                    "the attributes that are extracted",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)

        # Process the regex so we've got it ready for matching
        if self.options["regex"] is not None:
            # We've been given a regex directly: just compile this
            try:
                self.regex = re.compile(self.options["regex"])
            except Exception, e:
                # Any errors here should be reported as errors preparing the module info
                raise ModuleInfoLoadError("could not parse regex '%s': %s" % (self.options["regex"], e))
        elif self.options["expr"] is not None:
            # Parse the expression into a regex we can use for matching
            expression = self.options["expr"]
            pos_re = re.compile(r"[A-Z]+\*?")
            regex = ""

            for token in expression.split():
                if "=" in token:
                    # This is a variable assignment
                    var_name, __, pos = token.partition("=")
                    # Expression must be a POS
                    if not pos_re.match(token):
                        raise ModuleInfoLoadError("error in pos-text expression: variable binding must be on a "
                                                  "POS, can't match '%s' (for variable '%s')" % (pos, var_name))
                    regex += _pos_regex(pos, var_name)
                elif token.startswith("/") and token.endswith("/"):
                    # This is a regex to be applied to a word
                    regex += _regex_word_regex(token[1:-1])
                elif pos_re.match(token):
                    # This is a POS
                    regex += _pos_regex(token)
                else:
                    # Just a word
                    regex += _word_regex(token)
            # Start and end with a space
            regex += " "
            # Now try compiling this regex
            try:
                self.regex = re.compile(regex)
            except Exception, e:
                raise ModuleInfoLoadError("build regex from expression (%s), but couldn't compile it: %s" %
                                          (regex, e))
        else:
            raise ModuleInfoLoadError("pos text matcher must have either an expr or a regex option")


def _pos_regex(text, name=None):
    if name is None:
        # Just match the word to start with
        r = r" [!\|]*\|"
    else:
        # Match the word in a named group
        r = r" (?P<%s>[!\|]*)\|" % name

    if text.endswith("*"):
        # Match POS prefix
        return r + r"%s\S*" % text[:-1]
    else:
        # Match exact POS
        return r + r"%s" % text

def _word_regex(text):
    # Case-insensitively match the word, with no constraint on the POS tag
    return r" %s\|[A-Z]+" % "".join("[%s%s]" % (letter.lower(), letter.upper()) for letter in text)

def _regex_word_regex(text):
    # Include this regex in one that also eats up the POS tag
    return r" %s\|[A-Z]+" % text
