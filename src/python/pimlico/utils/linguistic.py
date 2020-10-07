# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import string
import re


# Handy list of pronouns
ENGLISH_PRONOUNS = [
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "myself", "yourself", "himself", "herself", "itself", "ourself", "ourselves", "themselves",
    "my", "your", "his", "its", "it's", "our", "their",
    "mine", "yours", "ours", "theirs",
    "this", "that", "those", "these"
]


RE_PUNCT = re.compile('([%s])+' % re.escape(string.punctuation))


def strip_punctuation(s, split_words=True):
    if split_words:
        return RE_PUNCT.sub(" ", s)
    else:
        return RE_PUNCT.sub("", s)
