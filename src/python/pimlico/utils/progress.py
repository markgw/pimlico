# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import warnings

from pimlico import cfg
from itertools import islice
from progressbar import Percentage, Bar, RotatingMarker, ETA, ProgressBar, Counter, UnknownLength


def get_progress_bar(maxval, counter=False, title=None, start=True):
    """
    Simple utility to build a standard progress bar, so I don't have to think about
    this each time I need one.
    Starts the progress bar immediately.

    start is no longer used, included only for backwards compatibility.

    """
    if cfg.NON_INTERACTIVE_MODE:
        # If we're not in interactive mode (e.g. piping to a file), don't output the progress bar
        # In future we might want to print things instead, but for now we just don't output anything
        return LittleOutputtingProgressBar(maxval)

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

    def increment(self):
        self.update(self.currval+1)


class DummyFileDescriptor(object):
    """
    Passed in to ProgressBar instead of a file descriptor (e.g. stderr) to ensure that
    nothing gets output.

    """
    def read(self, size=None):
        return None

    def readLine(self, size=None):
        return None

    def write(self, s):
        return

    def close(self):
        return


class NonOutputtingProgressBar(SafeProgressBar):
    """
    Behaves like ProgressBar, but doesn't output anything.

    """
    def __init__(self, *args, **kwargs):
        kwargs["fd"] = DummyFileDescriptor()
        super(NonOutputtingProgressBar, self).__init__(*args, **kwargs)


class LittleOutputtingProgressBar(SafeProgressBar):
    """
    Behaves like ProgressBar, but doesn't output much. Instead of constantly redrawing the
    progress bar line, it outputs a simple progress message every time it hits the next 10%
    mark.

    If running on a terminal, this will update the line, as with a normal progress bar.
    If piping to a file, this will just print a new line occasionally, so won't fill up your
    file with thousands of progress updates.

    """
    def __init__(self, *args, **kwargs):
        super(LittleOutputtingProgressBar, self).__init__(*args, **kwargs)
        self.output_start_end_only = False

        if self.maxval is UnknownLength:
            # Output only a start and end
            self.output_start_end_only = True
        else:
            self.num_intervals = 10
        self._time_sensitive = False

    def _current_percentage(self):
        return self.currval * 100 / self.maxval

    def _format_line(self):
        # Ignore widgets and output a simple message
        text = "Completed {}%".format(self._current_percentage())
        # Ignore justification: always L-justify
        return text.ljust(self.term_width)

    def _need_update(self):
        if self.output_start_end_only:
            return False
        else:
            return super(LittleOutputtingProgressBar, self)._need_update()

    def start(self):
        super(LittleOutputtingProgressBar, self).start()
        if self.output_start_end_only:
            self.fd.write("Started".ljust(self.term_width) + "\r")

        # This gets computed automatically on the basis of the terminal width, but we want it
        # set to a small value
        self.num_intervals = 10
        if self.maxval is not UnknownLength:
            if self.maxval < 0: raise ValueError('Value out of range')
            self.update_interval = self.maxval / self.num_intervals

    def finish(self):
        super(LittleOutputtingProgressBar, self).finish()
        self.fd.write("Finished\n")


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
