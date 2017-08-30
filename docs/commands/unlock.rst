.. _command_unlock:

unlock
~~~~~~


*Command-line tool subcommand*


Forcibly remove an execution lock from a module. If a lock has ended up
getting left on when execution exited prematurely, use this to remove it.

When a module starts running, it is locked to avoid making a mess of your output
data by running the same module from another terminal, or some other silly mistake
(I know, for some of us this sort of behaviour is frustratingly common).

Usually shouldn't be necessary, even if there's an error during execution, since the
module should be unlocked when Pimlico exits, but occasionally (e.g. if you have to
forcibly kill Pimlico during execution) the lock gets left on.


Usage:

::

    pimlico.sh [...] unlock module_name [-h]


Positional arguments
====================

+-----------------+----------------------------------------------+
| Arg             | Description                                  |
+=================+==============================================+
| ``module_name`` | The name (or number) of the module to unlock |
+-----------------+----------------------------------------------+

