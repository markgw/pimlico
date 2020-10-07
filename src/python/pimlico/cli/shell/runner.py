# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function
# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.cli.shell.base import DataShell, ShellError
from pimlico.cli.shell.commands import BASIC_SHELL_COMMANDS
from pimlico.cli.subcommands import PimlicoCLISubcommand


class ShellCLICmd(PimlicoCLISubcommand):
    command_name = "shell"
    command_help = "Open a shell to give access to the data output by a module"

    def add_arguments(self, parser):
        parser.add_argument("module_name", help="The name (or number) of the module whose output to look at")
        parser.add_argument("output_name", nargs="?", help="The name of the output from the module to browse. If blank, "
                                                           "load the default output")

    def run_command(self, pipeline, opts):
        module_name = opts.module_name
        output_name = opts.output_name
        print("Loading %s of module '%s'" % \
              ("default output" if output_name is None else "output '%s'" % output_name, module_name))
        setup = pipeline[module_name].get_output_reader_setup(output_name)
        if not setup.ready_to_read():
            raise ShellError("Output '{}' from module '{}' is not yet ready to read".format(
                module_name, output_name or "default"))
        reader = setup(pipeline, module_name)
        print("Datatype: %s\n" % reader.datatype.datatype_name)
        print("""
Pimlico dataset shell
=====================
The dataset shell provides you with a variety of ways to query the contents
of a Pimlico datatype instance. The commands you can use to query the
dataset depend on its datatype: some datatypes will provide their own set of
commands specific to the sort of data they contain.

For help on using any of the commands, use the 'help' command, with the
command name as an argument.

You can run arbitrary one-line Python commands, operating on the data reader 
using the name 'data' or 'reader'. The shell will try to execute anything you 
type that it doesn't recognise as an available command in this way.

For more a comprehensive Python interpreter, with the dataset and environment
available, use the 'py' command.

Type Ctrl+D to exit.
""")
        launch_shell(reader)


def launch_shell(data):
    """
    Starts a shell to view and query the given datatype instance.

    """
    commands = BASIC_SHELL_COMMANDS + data.datatype.shell_commands
    shell = DataShell(data, commands)
    print("Available commands for this datatype: %s" % ", ".join(
        "%s%s" % (c.commands[0],
                  " (%s)" % ", ".join(c.commands[1:]) if len(c.commands) > 1 else "") for c in commands))
    shell.cmdloop()
