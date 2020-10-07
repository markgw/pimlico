# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import object


class PimlicoCLISubcommand(object):
    """
    Base class for defining subcommands to the main command line tool.

    This allows us to split up subcommands, together with all their arguments/options and their functionality,
    since there are quite a lot of them.

    Documentation of subcommands should be supplied in the following ways:

       - Include help texts for positional args and options in the add_arguments() method. They will all be
         included in the doc page for the command.
       - Write a very short description of what the command is for (a few words) in command_desc. This
         will be used in the summary table / TOC in the docs.
       - Write a short description of what the command does in ``command_help``. This will be available in
         command-line help and used as a fallback if you don't do the next point.
       - Write a good guide to using the command (or at least say what it does) in the class' docstring (i.e.
         overriding this). This will form the bulk of the command's doc page.

    """
    command_name = None
    command_help = None
    command_desc = None

    def add_arguments(self, parser):
        pass

    def run_command(self, pipeline, opts):
        raise NotImplementedError
