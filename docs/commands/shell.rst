.. _command_shell:

shell
~~~~~


*Command-line tool subcommand*

Open a shell to give access to the data output by a module.


Usage:

::

    pimlico.sh [...] shell module_name [output_name] [-h]


Positional arguments
====================

+-------------------+-------------------------------------------------------------------------------------+
| Arg               | Description                                                                         |
+===================+=====================================================================================+
| ``module_name``   | The name (or number) of the module whose output to look at                          |
+-------------------+-------------------------------------------------------------------------------------+
| ``[output_name]`` | The name of the output from the module to browse. If blank, load the default output |
+-------------------+-------------------------------------------------------------------------------------+

