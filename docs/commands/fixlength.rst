.. _command_fixlength:

fixlength
~~~~~~~~~


*Command-line tool subcommand*


Under some circumstances (e.g. some unpredictable combinations of failures
and restarts), an output corpus can end up with an incorrect length in its
metadata. This command counts up the documents in the corpus and corrects
the stored length if it's wrong.


Usage:

::

    pimlico.sh [...] fixlength module [outputs [outputs ...]] [-h] [--dry]


Positional arguments
====================

+-----------------------------+----------------------------------------------------------+
| Arg                         | Description                                              |
+=============================+==========================================================+
| ``module``                  | The name (or number) of the module to recover            |
+-----------------------------+----------------------------------------------------------+
| ``[outputs [outputs ...]]`` | Names of module outputs to check. By default, checks all |
+-----------------------------+----------------------------------------------------------+

Options
=======

+-----------+------------------------------------------------------+
| Option    | Description                                          |
+===========+======================================================+
| ``--dry`` | Dry run: check the lengths, but don't write anything |
+-----------+------------------------------------------------------+

