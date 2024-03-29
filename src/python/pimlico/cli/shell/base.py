# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function
from builtins import object

import os
import readline
import traceback
from cmd import Cmd
from operator import itemgetter

from pimlico import LOG_DIR
from pimlico.utils.core import is_identifier

HISTORY_FILE = os.path.join(LOG_DIR, "data_shell_history")
# Limit stored history
readline.set_history_length(500)


class ShellCommand(object):
    """
    Base class used to provide commands for exploring a particular datatype. A basic set of commands is provided
    for all datatypes, but specific datatype classes may provide their own, by overriding the `shell_commands`
    attribute.

    """
    # List of command strings that trigger this command
    commands = []
    help_text = None

    def execute(self, shell, *args, **kwargs):
        """
        Execute the command. Get the dataset reader as shell.data.

        :param shell: DataShell instance. Reader available as shell.data
        :param args: Args given by the user
        :param kwargs: Named args given by the user as key=val
        """
        raise NotImplementedError


class DataShell(Cmd):
    """
    Terminal shell for querying datatypes.

    """
    prompt = ">>> "

    def __init__(self, data, commands, *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)
        self.data = data
        self.result_limit = 10

        readline.set_completer_delims(" ")

        # Index commands by their command strings for easy lookup
        self.commands = {}
        for command_obj in commands:
            for command_str in command_obj.commands:
                self.commands[command_str] = command_obj
        # Add help method for each command
        for command_name in self.commands:
            # We can only do this with command names that are valid Python identifiers
            if is_identifier(command_name):
                # Use closures to bind the command name
                def _get_help_cmd(slf, name):
                    def _help_cmd():
                        print(slf.commands[name].help_text)
                    return _help_cmd
                setattr(self, "help_%s" % command_name, _get_help_cmd(self, command_name))

                def _get_do_cmd(slf, name):
                    def _do_cmd(line):
                        slf._run_command(name, line.split())
                    return _do_cmd
                setattr(self, "do_%s" % command_name, _get_do_cmd(self, command_name))

        # Environment for executing Python commands
        # May get updated as time goes on
        self.env = {
            "data": self.data,
            "reader": self.data,
        }

    def get_names(self):
        # Overridden so it allows our help methods to be added dynamically
        return dir(self)

    def do_EOF(self, line):
        """ Exits the shell """
        print("\nExiting")
        return True

    def preloop(self):
        # Load shell history
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)

    def postloop(self):
        # Save shell history
        if not os.path.exists(os.path.dirname(HISTORY_FILE)):
            os.makedirs(os.path.dirname(HISTORY_FILE))
        readline.write_history_file(HISTORY_FILE)

    def emptyline(self):
        """ Don't repeat the last command (default): ignore empty lines """
        return

    def _run_command(self, cmd_name, parts):
        cmd = self.commands[cmd_name]
        # Process the rest of the line to get args and kwargs
        kwargs = dict(itemgetter(0, 2)(arg.partition("=")) for arg in parts if "=" in arg)
        args = [arg for arg in parts if "=" not in arg]
        cmd.execute(self, *args, **kwargs)

    def default(self, line):
        """
        We use this to handle commands that can't be handled using the `do_` pattern.
        Also handles the default fallback, which is to execute Python.

        """
        parts = line.split()
        if len(parts):
            if parts[0] in self.commands:
                self._run_command(parts[0], parts[1:])
            else:
                # If this isn't recognised as a command, try executing with Python interpreter
                exec(line, self.env)

    def cmdloop(self, intro=None):
        if intro or self.intro:
            print(intro or self.intro)

        while True:
            try:
                Cmd.cmdloop(self, intro="")
            except ShellError as e:
                print(e)
            except KeyboardInterrupt:
                print()
                self.postloop()
            except:
                # Print out the stack trace and return to the shell
                print("Error running command:")
                traceback.print_exc()
                self.postloop()
            else:
                self.postloop()
                break


class ShellError(Exception):
    pass
