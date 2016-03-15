from itertools import islice
from progressbar import Percentage, Bar, RotatingMarker, ETA, ProgressBar, Counter


def get_progress_bar(maxval, counter=False, title=None, start=True):
    """
    Simple utility to build a standard progress bar, so I don't have to think about
    this each time I need one.
    Starts the progress bar immediately.

    """
    widgets = []
    if title is not None:
        widgets.append("%s: " % title)
    widgets.extend([Percentage(), ' ', Bar(marker=RotatingMarker())])
    if counter:
        widgets.extend([' (', Counter(), ')'])
    widgets.extend([' ', ETA()])
    pbar = ProgressBar(widgets=widgets, maxval=maxval)
    if start:
        pbar.start()
    return pbar


def slice_progress(iterable, num_items, title=None):
    pbar = get_progress_bar(num_items, title=title)
    items = []
    for i, item in enumerate(islice(iterable, num_items)):
        items.append(item)
        pbar.update(i)
    pbar.finish()
    return items


def iter_progress(iterable, num_items, title=None):
    pbar = get_progress_bar(num_items, title=title)
    for i, item in enumerate(iterable):
        yield item
        if i < num_items:
            pbar.update(i)
    pbar.finish()


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
        return iter_progress(self.iterable, len(self), title=title)
