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

