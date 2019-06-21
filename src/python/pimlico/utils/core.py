# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import range
from builtins import object
from contextlib import contextmanager
import sys
import ast

import math


@contextmanager
def multiwith(*managers):
    """
    Taken from contextlib's nested(). We need the variable number of context managers that this function allows.

    """
    exits = []
    vars = []
    exc = (None, None, None)

    try:
        for mgr in managers:
            exit = mgr.__exit__
            enter = mgr.__enter__
            vars.append(enter())
            exits.append(exit)
        yield vars
    except:
        exc = sys.exc_info()
    finally:
        while exits:
            exit = exits.pop()
            try:
                if exit(*exc):
                    exc = (None, None, None)
            except:
                exc = sys.exc_info()

        if exc != (None, None, None):
            # Don't rely on sys.exc_info() still containing
            # the right information. Another exception may
            # have been raised and caught by an exit method
            raise exc[0], exc[1], exc[2]


def is_identifier(ident):
    """Determines if string is valid Python identifier."""
    # Smoke test - if it's not string, then it's not identifier
    if not isinstance(ident, str):
        return False

    # Resulting AST of simple identifier is <Module [<Expr <Name "foo">>]>
    try:
        root = ast.parse(ident)
    except SyntaxError:
        return False

    if not isinstance(root, ast.Module):
        return False
    if len(root.body) != 1:
        return False
    if not isinstance(root.body[0], ast.Expr):
        return False
    if not isinstance(root.body[0].value, ast.Name):
        return False
    if root.body[0].value.id != ident:
        return False
    return True


def remove_duplicates(lst, key=lambda x: x):
    """
    Remove duplicate values from a list, keeping just the first one, using a particular key function to compare them.

    """
    seen = set()
    seen_add = seen.add
    return [x for x in lst if key(x) not in seen and not seen_add(key(x))]


def infinite_cycle(iterable):
    """
    Iterate infinitely over the given iterable.

    Watch out for calling this on a generator or iter: they can only be iterated over once, so
    you'll get stuck in an infinite loop with no more items yielded once you've gone over it once.

    You may also specify a callable, in which case it will be called each time to get a new
    iterable/iterator. This is useful in the case of generator functions.

    :param iterable: iterable or generator to loop over indefinitely
    """
    from types import GeneratorType
    # Check whether iterable is a generator, and don't allow it, as it will lead to an infinite loop
    if isinstance(iterable, GeneratorType):
        raise TypeError("called infinite_cycle() on a generator: this will lead to getting stuck in an "
                        "infinite loop after the first full iteration")

    # Make a non-callable (i.e. simple iterable) into a callable so we can treat them in the same way
    if not callable(iterable):
        simple_iterable = iterable
        iterable = lambda: simple_iterable

    while True:
        for x in iterable():
            yield x


def import_member(path):
    """
    Import a class, function, or other module member by its fully-qualified Python name.

    :param path: path to member, including full package path and class/function/etc name
    :return: cls
    """
    from importlib import import_module

    mod_path, __, cls_name = path.rpartition(".")
    if not len(mod_path):
        raise ImportError("no module name in {}".format(path))
    try:
        mod = import_module(mod_path)
    except ImportError as e:
        raise ImportError("class' module does not exist: %s. %s" % (mod_path, e))

    if not hasattr(mod, cls_name):
        raise ImportError("could not load class %s from module %s: name does not exist" % (cls_name, mod_path))
    return getattr(mod, cls_name)


def split_seq(seq, separator, ignore_empty_final=False):
    """
    Iterate over a sequence and group its values into lists, separated in the original sequence by the given value.
    If `on` is callable, it is called on each element to test whether it is a separator. Otherwise, elements that
    are equal to `on` a treated as separators.

    :param seq: sequence to divide up
    :param separator: separator or separator test function
    :param ignore_empty_final: by default, if there's a separator at the end, the last sequence yielded is empty. If
        ignore_empty_final=True, in this case the last empty sequence is dropped
    :return: iterator over subsequences
    """
    if not callable(separator):
        is_separator = lambda x: x == separator
    else:
        is_separator = separator

    subsequence = []
    for elem in seq:
        if is_separator(elem):
            # Reached a separator, return the current subsequence and start accumulating values again
            yield subsequence
            subsequence = []
        else:
            subsequence.append(elem)
    if not ignore_empty_final or len(subsequence):
        # Yield the subsequence after the last separator, even if it's empty, unless ignore_empty_final given
        yield subsequence


def split_seq_after(seq, separator):
    """
    Somewhat like split_seq, but starts a new subsequence after each separator, without removing the
    separators. Each subsequence therefore ends with a separator, except the last one if there's no separator
    at the end.

    :param seq: sequence to divide up
    :param separator: separator or separator test function
    :return: iterator over subsequences
    """
    if not callable(separator):
        is_separator = lambda x: x == separator
    else:
        is_separator = separator

    subsequence = []
    for elem in seq:
        subsequence.append(elem)
        if is_separator(elem):
            # Reached a separator, return the current subsequence and start accumulating values again
            yield subsequence
            subsequence = []
    if len(subsequence):
        # Yield the subsequence after the last separator, unless it's empty
        yield subsequence


def chunk_list(lst, length):
    """
    Divides a list into chunks of max `length` length.
    """
    return [
        lst[i*length:(i+1)*length] for i in range(int(math.ceil(float(len(lst)) / length)))
    ]


class cached_property(object):
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.

    Often useful in Pimlico datatypes, where it can be time-consuming to load data,
    but we can't do it once when the datatype is first loaded, since the data might
    not be ready at that point. Instead, we can access the data, or particular
    parts of it, using properties and easily cache the result.

    Taken from: https://github.com/bottlepy/bottle

    """
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
