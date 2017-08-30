.. _command_clean:

clean
~~~~~


*Command-line tool subcommand*


Cleans up module output directories that have got left behind.

Often, when developing a pipeline incrementally, you try out some modules, but then remove them, or
rename them to something else. The directory in the Pimlico output store that was created to contain
their metadata, status and output data is then left behind and no longer associated with any module.

Run this command to check all storage locations for such directories. If it finds any, it prompts you
to confirm before deleting them. (If there are things in the list that don't look like they were left
behind by the sort of things mentioned above, don't delete them! I don't want you to lose your precious
output data if I've made a mistake in this command.)

Note that the operation of this command is specific to the loaded pipeline variant. If you have multiple
variants, make sure to select the one you want to clean with the general `--variant` option.


Usage:

::

    pimlico.sh [...] clean [-h]


