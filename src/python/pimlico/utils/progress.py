# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import warnings

from itertools import islice
from progressbar import Percentage, Bar, RotatingMarker, ETA, ProgressBar, Counter, UnknownLength


def get_progress_bar(maxval, counter=False, title=None, start=True):
    """
    Simple utility to build a standard progress bar, so I don't have to think about
    this each time I need one.
    Starts the progress bar immediately.

    start is no longer used, included only for backwards compatibility.

    """
    widgets = []
    if title is not None:
        widgets.append("%s: " % title)
    widgets.extend([Percentage(), ' ', Bar(marker=RotatingMarker())])
    if counter:
        widgets.extend([' (', Counter(), ')'])
    widgets.extend([' ', ETA()])
    pbar = SafeProgressBar(widgets=widgets, maxval=maxval)
    return pbar


class SafeProgressBar(ProgressBar):
    """
    Override basic progress bar to wrap update() method with a couple of extra features.

    1. You don't need to call start() -- it will be called when the first update is received. This is good for
       processes that have a bit of a start-up lag, or where starting to iterate might generate some other output.
    2. An error is not raised if you update with a value higher than maxval. It's the most annoying thing ever if
       you run a long process and the whole thing fails near the end because you slightly miscalculated maxval.

    """
    def update(self, value=None):
        if self.start_time is None:
            self.start()
        if self.maxval == 0:
            return

        if value is not None and value is not UnknownLength and \
                self.maxval is not UnknownLength and not 0 <= value <= self.maxval:
            # Catch out-of-range updates and don't let progress bar raise an exception
            warnings.warn("Progress bar received update out of range (max=%s)" % self.maxval)
        else:
            super(SafeProgressBar, self).update(value)


def slice_progress(iterable, num_items, title=None):
    pbar = get_progress_bar(num_items, title=title)
    items = []
    for i, item in enumerate(islice(iterable, num_items)):
        items.append(item)
        pbar.update(i)
    pbar.finish()
    return items


class ProgressBarIter(object):
    def __init__(self, iterable, title=None):
        self.title = title
        self.iterable = iterable
        self._iteration = 0

    def __len__(self):
        return len(self.iterable)

    def __iter__(self):
        if isinstance(self.title, (list, tuple)):
            if self._iteration >= len(self.title):
                # No more titles left: use the last one again
                title = self.title[-1]
            else:
                title = self.title[self._iteration]
        else:
            title = self.title
        self._iteration += 1
        pbar = get_progress_bar(len(self), title=title)
        return pbar(self.iterable)
