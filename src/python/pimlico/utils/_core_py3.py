
def raise_from(exc, cause):
    """
    Like future's raise_from function. However, on Py3, just calls raise X from Y.
    On Py2, defers to future's replacement.

    This means that we get the full functionality of raise from on PY3, which
    is our main priority. If you run on PY2, you get less debugging information
    in some cases, but that's no reason to ruin the debugging information on PY3 too!

    """
    raise exc from cause
