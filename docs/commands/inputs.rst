.. _command_inputs:

inputs
~~~~~~


*Command-line tool subcommand*

Show the locations of the inputs of a given module. If the input datasets are available, their actual location is shown. Otherwise, all directories in which the data is being checked for are shown.


Usage:

::

    pimlico.sh [...] inputs module_name [-h]


Positional arguments
====================

+-----------------+-------------------------------------------------------------------+
| Arg             | Description                                                       |
+=================+===================================================================+
| ``module_name`` | The name (or number) of the module to display input locations for |
+-----------------+-------------------------------------------------------------------+

