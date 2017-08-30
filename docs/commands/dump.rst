.. _command_dump:

dump
~~~~


*Command-line tool subcommand*


Dump the entire available output data from a given pipeline module to a
tarball, so that it can easily be loaded into the same pipeline on another
system. This is primarily to support spreading the execution of a pipeline
between multiple machines, so that the output from a module can easily be
transferred and loaded into a pipeline.

Dump to a tarball using this command, transfer the file between machines and
then run the :doc:`load command </commands/load>` to import it there.

.. seealso::

   :doc:`/guides/multiple_servers`: for a more detailed guide to transferring data across servers.


Usage:

::

    pimlico.sh [...] dump [modules [modules ...]] [-h] [--output OUTPUT]


Positional arguments
====================

+-----------------------------+----------------------------------------------------------------------------------------------------------------+
| Arg                         | Description                                                                                                    |
+=============================+================================================================================================================+
| ``[modules [modules ...]]`` | Names or numbers of modules whose data to dump. If multiple are given, a separate file will be dumped for each |
+-----------------------------+----------------------------------------------------------------------------------------------------------------+

Options
=======

+----------------------+-------------------------------------------------------------------------------+
| Option               | Description                                                                   |
+======================+===============================================================================+
| ``--output``, ``-o`` | Path to directory to output to. Defaults to the current user's home directory |
+----------------------+-------------------------------------------------------------------------------+

