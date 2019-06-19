# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Basic set of shell commands that are always available.

"""
from __future__ import print_function
from pimlico.cli.shell.base import ShellCommand


class MetadataCmd(ShellCommand):
    commands = ["metadata"]
    help_text = "Display the loaded dataset's metadata"

    def execute(self, shell, *args, **kwargs):
        metadata = shell.data.metadata
        print("\n".join("%s: %s" % (key, val) for (key, val) in metadata.iteritems()))


class PythonCmd(ShellCommand):
    commands = ["python", "py"]
    help_text = "Run a Python interpreter using the current environment, including import availability of " \
                "all the project code, as well as the dataset in the 'data' variable"

    def execute(self, shell, *args, **kwargs):
        from code import interact
        import sys
        # Customize the prompt so we see that we're in the interpreter
        sys.ps1 = "py>> "
        sys.ps2 = "py.. "
        print("Entering Python interpreter. Type Ctrl+D to exit\n")
        # Enter the interpreter
        interact(local=shell.env)
        print("Leaving Python interpreter")


BASIC_SHELL_COMMANDS = [MetadataCmd(), PythonCmd()]
