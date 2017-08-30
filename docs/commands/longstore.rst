.. _command_longstore:

longstore
~~~~~~~~~


*Command-line tool subcommand*

Move a particular module's output from the short-term store to the long-term store. It will still be found here by input readers. You might want to do this if your long-term store is bigger, to keep down the short-term store size.


Usage:

::

    pimlico.sh [...] longstore [modules [modules ...]] [-h]


Positional arguments
====================

+-----------------------------+-----------------------------------------------------------+
| Arg                         | Description                                               |
+=============================+===========================================================+
| ``[modules [modules ...]]`` | The names (or numbers) of the module whose output to move |
+-----------------------------+-----------------------------------------------------------+

