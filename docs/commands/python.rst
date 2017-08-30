.. _command_python:

python
~~~~~~


*Command-line tool subcommand*

Load the pipeline config and enter a Python interpreter with access to it in the environment.


Usage:

::

    pimlico.sh [...] python [script] [-h] [-i]


Positional arguments
====================

+--------------+---------------------------------------------------+
| Arg          | Description                                       |
+==============+===================================================+
| ``[script]`` | Script file to execute. Omit to enter interpreter |
+--------------+---------------------------------------------------+

Options
=======

+--------+----------------------------------------------+
| Option | Description                                  |
+========+==============================================+
| ``-i`` | Enter interactive shell after running script |
+--------+----------------------------------------------+

