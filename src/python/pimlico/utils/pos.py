# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

# CCGBank has some POS tags not in the PTB tagset
CCGBANK_TO_PTB_POS_MAP = {
    "RRB": ")",
    "LRB": "(",
    "SO": "RB",
    "LQU": "``",
    "RQU": "''",
}

# This is the set of POS tags the Malt pre-trained model recognises, namely the PTB extended tagset
# If Malt gets something outside this set it will fail
PTB_POS_TAGS = [
    "IN", "DT", "NNP", "CD", "NN", "``", "''", "POS", "(", "VBN", "NNS", "VBP", ",", "CC", ")", "VBD", "RB", "TO",
    ".", "VBZ", "NNPS", "PRP", "PRP$", "VB", "JJ", "MD", "VBG", "RBR", ":", "WP", "WDT", "JJR", "PDT", "RBS", "WRB",
    "JJS", "$", "RP", "FW", "EX", "SYM", "#", "LS", "UH", "WP$", "PRT"
]

def pos_tag_to_ptb(tag):
    """
    see :doc:pos_pos_tags_to_ptb

    """
    if tag in PTB_POS_TAGS:
        # Fine already
        return tag
    elif tag in CCGBANK_TO_PTB_POS_MAP:
        # Perform the CCGBank mapping
        return CCGBANK_TO_PTB_POS_MAP[tag]
    else:
        raise NonPTBTagError("POS tag '%s' is not a valid PTB tag" % tag)


def pos_tags_to_ptb(tags):
    """
    Takes a list of POS tags and checks they're all in the PTB tagset. If they're not, tries mapping them according
    to CCGBank's special version of the tagset. If that doesn't work, raises a NonPTBTagError.

    """
    return map(pos_tag_to_ptb, tags)


class NonPTBTagError(Exception):
    pass
