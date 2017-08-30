.. _command_load:

load
~~~~


*Command-line tool subcommand*


Load the output data for a given pipeline module from a tarball previously created by the
`dump` command (typically on another machine).
This is primarily to support spreading the execution of a pipeline
between multiple machines, so that the output from a module can easily be
transferred and loaded into a pipeline.

Dump to a tarball using the :doc:`dump command </commands/dump>`,
transfer the file between machines and
then run this command to import it there.

.. seealso::

   :doc:`/guides/multiple_servers`: for a more detailed guide to transferring data across servers.


Usage:

::

    pimlico.sh [...] load [paths [paths ...]] [-h] [--force-overwrite]


Positional arguments
====================

+-------------------------+----------------------------------------------------------+
| Arg                     | Description                                              |
+=========================+==========================================================+
| ``[paths [paths ...]]`` | Paths to dump files (tarballs) to load into the pipeline |
+-------------------------+----------------------------------------------------------+

Options
=======

+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Option                        | Description                                                                                                                                                 |
+===============================+=============================================================================================================================================================+
| ``--force-overwrite``, ``-f`` | If data already exists for a module being imported, overwrite without asking. By default, the user will be prompted to check whether they want to overwrite |
+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+

