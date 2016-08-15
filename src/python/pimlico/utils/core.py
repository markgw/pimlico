# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from contextlib import contextmanager
import sys
import ast


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
    while True:
        for x in iterable:
            yield x


def import_member(path):
    """
    Import a class, function, or other module member by its fully-qualified Python name.

    :param path: path to member, including full package path and class/function/etc name
    :return: cls
    """
    from importlib import import_module

    mod_path, __, cls_name = path.rpartition(".")
    try:
        mod = import_module(mod_path)
    except ImportError, e:
        raise ImportError("class' module does not exist: %s. %s" % (mod_path, e))

    if not hasattr(mod, cls_name):
        raise ImportError("could not load class %s from module %s: name does not exist" % (cls_name, mod_path))
    return getattr(mod, cls_name)


def split_seq(seq, separator):
    """
    Iterate over a sequence and group its values into lists, separated in the original sequence by the given value.
    If `on` is callable, it is called on each element to test whether it is a separator. Otherwise, elements that
    are equal to `on` a treated as separators.

    :param seq: sequence to divide up
    :param separator: separator or separator test function
    :return: iterator over subsequences
    """
    if not callable(separator):
        separator = lambda x: x == separator

    subsequence = []
    for elem in seq:
        if separator(elem):
            # Reached a separator, return the current subsequence and start accumulating values again
            yield subsequence
            subsequence = []
        else:
            subsequence.append(elem)
    # Yield the subsequence after the last separator, even if it's empty
    yield subsequence
