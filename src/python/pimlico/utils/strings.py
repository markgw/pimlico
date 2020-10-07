# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import zip


def truncate(s, length, ellipsis=u"..."):
    if len(s) > length:
        return u"%s%s" % (s[:length-len(ellipsis)].strip(), ellipsis)
    else:
        return s


def similarities(targets, reference):
    """
    Compute string similarity of each of a list of targets to a given reference string.
    Uses `difflib.SequenceMatcher` to compute similarity.

    :param reference: compare all strings to this one
    :param targets: list of targets to measure similarity of
    :return: list of similarity values
    """
    from difflib import SequenceMatcher

    matcher = SequenceMatcher()
    matcher.set_seq2(reference)

    sims = []
    for target in targets:
        matcher.set_seq1(target)
        sims.append(matcher.ratio())
    return sims


def sorted_by_similarity(targets, reference):
    """
    Return target list sorted by similarity to the reference string.
    See :func:similarities for similarity measurement.

    """
    from operator import itemgetter

    targets = list(targets)
    sims = similarities(targets, reference)
    return [trg for (trg, sim) in reversed(sorted(zip(targets, sims), key=itemgetter(1)))]

