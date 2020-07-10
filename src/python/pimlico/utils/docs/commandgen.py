# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool to generate Pimlico command docs. Based on Sphinx's apidoc tool.

"""
from __future__ import print_function
from builtins import str
from builtins import zip
from builtins import range

import argparse
import os
import re
from argparse import SUPPRESS, OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER
from operator import itemgetter
from sphinx import __version__
from .rest import format_heading

from pimlico import install_core_dependencies
from pimlico.cli.main import SUBCOMMANDS
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.utils.docs.rest import make_table


def generate_docs(output_dir):
    """
    Generate RST docs for Pimlico commands and output to a directory.

    """
    command_names, command_descs = list(zip(*(
        generate_docs_for_command(command, output_dir) for command in SUBCOMMANDS
    )))

    # Generate an index for all commands
    generate_contents_page(command_names, command_descs, output_dir)


def generate_docs_for_command(command_cls, output_dir):
    command_name = command_cls.command_name
    print("Building docs for %s" % command_name)

    # Instantiate the subcommand, so we can manipulate arguments
    command = command_cls()

    command_doc = command_cls.__doc__
    base_command_doc = PimlicoCLISubcommand.__doc__
    command_help = command_cls.command_help

    # Work out what text to use
    # If the command hasn't overridden the base command's doc, don't use that
    if command_doc is None or command_doc == base_command_doc:
        # Fall back to using the help text, if that's available
        if command_help is not None:
            doc_text = command_help
        else:
            # No documentation available
            doc_text = ""
    else:
        doc_text = strip_common_indent(command_doc)
    if doc_text:
        doc_text = "%s." % doc_text.rstrip("\n. ")

    if command.command_desc is not None:
        # Description supplied -- best practice
        command_short_desc = command.command_desc
    elif command_help is not None:
        # No description, but help text: use that instead
        command_short_desc = command_help.strip()
        if len(command_short_desc) > 500:
            command_short_desc = command_short_desc[:497] + "..."
    else:
        command_short_desc = None

    # We have to create an argument parser and get the command to add its args to it, so we can see what they are
    arg_parser = argparse.ArgumentParser()
    command.add_arguments(arg_parser)
    # Now we have to do some sneaky peaking into the arg parser
    # Pull information out of the argparser actions, following the procedure argparse uses for printing help
    optionals = []
    positionals = []
    for action in arg_parser._actions:
        if action.option_strings:
            optionals.append(action)
        else:
            positionals.append(action)

    # Collect all actions' format strings
    parts = []
    for i, action in enumerate(positionals + optionals):
        # Produce all arg strings
        if not action.option_strings:
            # Positional arg
            # Add the action string to the list
            parts.append(_format_args(action, action.dest))
        else:
            # Produce the first way to invoke the option in brackets
            option_string = action.option_strings[0]

            if action.nargs == 0:
                # If the Optional doesn't take a value, format is:
                #    -s or --long
                part = '%s' % option_string
            else:
                # If the Optional takes a value, format is:
                #    -s ARGS or --long ARGS
                default = action.dest.upper()
                args_string = _format_args(action, default)
                part = '%s %s' % (option_string, args_string)
            # Make it look optional if it's not required or in a group
            if not action.required:
                part = '[%s]' % part
            parts.append(part)

    usage = "pimlico.sh [...] %s %s" % (command_name, " ".join(parts))

    args_table = [
        [
            "``%s``" % _format_args(action, action.dest),
            cap_first(action.help) if action.help is not SUPPRESS else "",
        ] for action in positionals
    ]

    # Put together the options table
    options_table = [
        [
            ", ".join("``%s``" % s for s in action.option_strings),
            cap_first(action.help) if action.help is not SUPPRESS else "",
        ]
        for action in optionals
        # Skip the --help option always, since it's on every command and doesn't look good in the docs
        if "--help" not in action.option_strings
    ]

    filename = os.path.join(output_dir, "%s.rst" % command_name)
    with open(filename, "w") as output_file:
        # Add a label that we can use to link to this doc elsewhere in the docs
        output_file.write(".. _command_%s:\n\n" % command_name)
        # Make a page heading
        output_file.write(format_heading(0, "%s" % command_name))
        output_file.write("\n*Command-line tool subcommand*\n\n")
        # Insert text from docstrings
        output_file.write(doc_text + "\n\n\n")
        # Include usage
        output_file.write("Usage:\n\n::\n\n    %s\n\n\n" % usage)

        # Output a table of inputs
        if args_table:
            output_file.write(format_heading(1, "Positional arguments"))
            output_file.write("%s\n" % make_table(args_table, header=["Arg", "Description"]))

        # Table of outputs
        if options_table:
            output_file.write(format_heading(1, "Options"))
            output_file.write("%s\n" % make_table(options_table, header=["Option", "Description"]))

    return command_name, command_short_desc


def _format_args(action, default_metavar):
    if action.metavar is not None:
        metavar_result = action.metavar
    elif action.choices is not None:
        choice_strs = [str(choice) for choice in action.choices]
        metavar_result = '{%s}' % ','.join(choice_strs)
    else:
        metavar_result = default_metavar

    if isinstance(metavar_result, tuple):
        get_metavar = lambda x: metavar_result
    else:
        get_metavar = lambda tuple_size: (metavar_result, ) * tuple_size

    if action.nargs is None:
        part = '%s' % get_metavar(1)
    elif action.nargs == OPTIONAL:
        part = '[%s]' % get_metavar(1)
    elif action.nargs == ZERO_OR_MORE:
        part = '[%s [%s ...]]' % get_metavar(2)
    elif action.nargs == ONE_OR_MORE:
        part = '%s [%s ...]' % get_metavar(2)
    elif action.nargs == REMAINDER:
        part = '...'
    elif action.nargs == PARSER:
        part = '%s ...' % get_metavar(1)
    else:
        formats = ['%s' for _ in range(action.nargs)]
        part = ' '.join(formats) % get_metavar(action.nargs)
    return part


def generate_contents_page(commands, command_descs, output_dir):
    print("Building contents page (index.rst)")
    command_table = [
        [":doc:`%s`" % name, desc] for (name, desc) in sorted(zip(commands, command_descs), key=itemgetter(0))
    ]

    with open(os.path.join(output_dir, "index.rst"), "w") as index_file:
        index_file.write("""\
{title}

The main Pimlico command-line interface (usually accessed via `pimlico.sh` in your project root)
provides subcommands to perform different operations. Call it like so, using one of the subcommands
documented below to access particular functionality:

.. code-block:: bash

   ./pimlico.sh <config-file> [general options...] <subcommand> [subcommand args/options]

The commands you are likely to use most often are: :doc:`status`, :doc:`run`, :doc:`reset` and maybe :doc:`browse`.

For a reference for each command's options, see the command-line documentation: ``./pimlico.sh --help``, for
a general reference and ``./pimlico.sh <config_file> <command> --help`` for a specific subcommand's
reference.

Below is a more detailed guide for each subcommand, including all of the documentation available via the
command line.


{table}

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

   {list}
""".format(
            title=format_heading(0, "Command-line interface"),
            table=make_table(command_table),
            list="\n   ".join(commands),
        ))


def cap_first(txt):
    if len(txt) > 0:
        return txt[0].upper() + txt[1:]
    else:
        return txt


_find_non_space = re.compile('[^ ]').search


def strip_common_indent(code):
    # Taken from h5py source
    min_indent = None
    lines = code.splitlines()
    for line in lines:
        match = _find_non_space(line)
        if not match:
            continue  # blank
        indent = match.start()
        if line[indent] == '#':
            continue  # comment
        if min_indent is None or min_indent > indent:
            min_indent = indent
    for ix, line in enumerate(lines):
        match = _find_non_space(line)
        if not match or not line or line[indent:indent+1] == '#':
            continue
        lines[ix] = line[min_indent:]
    return '\n'.join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate command documentation RST files from core Pimlico "
                                                 "command-line commands")
    parser.add_argument("output_dir", help="Where to put the .rst files")
    opts = parser.parse_args()

    output_dir = os.path.abspath(opts.output_dir)

    # Install basic Pimlico requirements
    install_core_dependencies()

    print("Sphinx %s" % __version__)
    print("Pimlico command doc generator")
    print("Outputting module docs to %s" % output_dir)

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    generate_docs(output_dir)
