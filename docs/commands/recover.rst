.. _command_recover:

recover
~~~~~~~


*Command-line tool subcommand*


When a document map module gets killed forcibly, sometimes it doesn't have time to
save its execution state, meaning that it can't pick up from where it left off.

This command tries to fix the state so that execution can be resumed. It counts
the documents in the output corpora and checks what the last written document was.
It then updates the state to mark the module as partially executed, so that it
continues from this document when you next try to run it.

The last written document is always thrown away, since we don't know whether it
was fully written. To avoid partial, broken output, we assume the last document
was not completed and resume execution on that one.

Note that this will only work for modules that output something (which may be an
invalid doc) to every output for every input doc. Modules that only output to
some outputs for each input cannot be recovered so easily.


Usage:

::

    pimlico.sh [...] recover module [-h] [--dry] [--last-docs LAST_DOCS]


Positional arguments
====================

+------------+-----------------------------------------------+
| Arg        | Description                                   |
+============+===============================================+
| ``module`` | The name (or number) of the module to recover |
+------------+-----------------------------------------------+

Options
=======

+-----------------+------------------------------------------------------------------+
| Option          | Description                                                      |
+=================+==================================================================+
| ``--dry``       | Dry run: just say what we'd do                                   |
+-----------------+------------------------------------------------------------------+
| ``--last-docs`` | Number of last docs to look at in each corpus when synchronizing |
+-----------------+------------------------------------------------------------------+

