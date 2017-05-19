# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool to generate Pimlico command docs. Based on Sphinx's apidoc tool.

"""
import argparse
import os
import warnings
from argparse import SUPPRESS, OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER
from importlib import import_module
from sphinx import __version__
from sphinx.apidoc import format_heading

from pimlico import install_core_dependencies
from pimlico.cli.main import SUBCOMMANDS
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.core.modules.options import format_option_type
from pimlico.datatypes.base import DynamicOutputDatatype, PimlicoDatatype, MultipleInputs
from pimlico.utils.docs import trim_docstring
from pimlico.utils.docs.rest import make_table


def generate_docs(output_dir):
    """
    Generate RST docs for Pimlico commands and output to a directory.

    """
    generated_commands = []
    for command in SUBCOMMANDS:
        generate_docs_for_command(command, output_dir)
        generated_commands.append(command.command_name)

    # Generate an index for all commands
    generate_contents_page(generated_commands, output_dir)


def generate_docs_for_command(command, output_dir):
    command_name = command.command_name
    print "Building docs for %s" % command_name

    command_doc = command.__doc__
    base_command_doc = PimlicoCLISubcommand.__doc__
    command_help = command.command_help

    # We out what text to use
    # If the command hasn't overridden the base command's doc, don't use that
    if command_doc == base_command_doc:
        # Fall back to using the help text, if that's available
        if command_help is not None:
            doc_text = command_help
        else:
            # No documentation available
            doc_text = ""
    else:
        doc_text = command_doc

    # We have to create an argument parser and get the command to add its args to it, so we can see what they are
    arg_parser = argparse.ArgumentParser()
    command.add_arguments(arg_parser)
    # Now we have to do some sneaky peaking into the arg parser
    arg_actions = arg_parser._actions + sum((g._actions for g in arg_parser._action_groups), [])

    # Pull information out of the argparser actions, following the procedure argparse uses for printing help
    optionals = []
    positionals = []
    for action in arg_actions:
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

    # insert things at the necessary indices
    for i in sorted(inserts, reverse=True):
        parts[i:i] = [inserts[i]]

    # join all the action items with spaces
    text = ' '.join([item for item in parts if item is not None])

    # clean up separators for mutually exclusive groups
    open = r'[\[(]'
    close = r'[\])]'
    text = _re.sub(r'(%s) ' % open, r'\1', text)
    text = _re.sub(r' (%s)' % close, r'\1', text)
    text = _re.sub(r'%s *%s' % (open, close), r'', text)
    text = _re.sub(r'\(([^|]*)\)', r'\1', text)
    text = text.strip()


    # Put together the options table
    options_table = [
        [
            option_name,
            "(required) " if d.get("required", False) else "" + d.get("help", ""),
            format_option_type(d.get("type", str)),
        ]
        for (option_name, d) in ModuleInfo.module_options.items()
    ]

    filename = os.path.join(output_dir, "%s.rst" % module_path)
    with open(filename, "w") as output_file:
        # Make a page heading
        output_file.write(format_heading(0, ModuleInfo.module_readable_name or ModuleInfo.module_type_name))
        # Add a directive to mark this as the documentation for the py module that defines the Pimlico module
        output_file.write(".. py:module:: %s\n\n" % module_path)
        # Output a summary table of key information
        output_file.write("%s\n" % make_table(key_info))
        # Insert text from docstrings
        if info_doc is not None:
            output_file.write(trim_docstring(info_doc) + "\n\n")
        if module_info_doc is not None:
            output_file.write(trim_docstring(module_info_doc) + "\n\n")
        output_file.write("\n")
        output_file.write("".join("%s\n\n" % para for para in additional_paras))

        # Output a table of inputs
        output_file.write(format_heading(1, "Inputs"))
        if input_table:
            output_file.write("%s\n" % make_table(input_table, header=["Name", "Type(s)"]))
        else:
            output_file.write("No inputs\n")

        # Table of outputs
        output_file.write(format_heading(1, "Outputs"))
        if output_table:
            output_file.write("%s\n" % make_table(output_table, header=["Name", "Type(s)"]))
        elif optional_output_table:
            output_file.write("No non-optional outputs\n")
        else:
            output_file.write("No outputs\n")
        if optional_output_table:
            output_file.write("\n" + format_heading(2, "Optional"))
            output_file.write("%s\n" % make_table(optional_output_table, header=["Name", "Type(s)"]))

        # Table of options
        if options_table:
            output_file.write(format_heading(1, "Options"))
            output_file.write("%s\n" % make_table(options_table, header=["Name", "Description", "Type"]))
    return ModuleInfo


def _format_args(action, default_metavar)
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


def input_datatype_list(types):
    if type(types) is tuple:
        # This is a list of types
        return " or ".join(input_datatype_text(t) for t in types)
    else:
        # Just a single type
        return input_datatype_text(types)


def input_datatype_text(datatype):
    if isinstance(datatype, type) and issubclass(datatype, PimlicoDatatype):
        # Standard behaviour for normal datatypes
        return ":class:`%s <%s>`" % (datatype.__name__, datatype.datatype_full_class_name())
    elif isinstance(datatype, MultipleInputs):
        # Multiple inputs, but the datatype is known: call this function to format the common type
        return ":class:`list <pimlico.datatypes.base.MultipleInputs>` of %s" % \
               input_datatype_text(datatype.datatype_requirements)
    elif datatype.datatype_doc_info is not None:
        # Dynamic input type that gives us a name to use
        return datatype.datatype_doc_info
    else:
        # Dynamic datatype requirement with no custom string
        return ":class:`%s <%s.%s>`" % (type(datatype).__name__, type(datatype).__module__, type(datatype).__name__)


def output_datatype_text(datatype):
    if isinstance(datatype, DynamicOutputDatatype):
        # Use the datatype name given by the dynamic datatype and link to the class
        datatype_class = datatype.get_base_datatype_class()
        if datatype_class is not None:
            datatype_class_name = datatype_class.datatype_full_class_name()
        else:
            # Just link to the dynamic datatype class
            datatype_class_name = "%s.%s" % (type(datatype).__module__, type(datatype).__name__)
        datatype_name = datatype.datatype_name or type(datatype).__name__
        return ":class:`%s <%s>`" % (datatype_name, datatype_class_name)
    else:
        class_name = datatype.datatype_full_class_name()
        # Allow non-class datatypes to be specified in the string
        if class_name.startswith(":"):
            return class_name
        else:
            return ":class:`~%s`" % datatype.datatype_full_class_name()


def generate_contents_page(commands, output_dir):
    with open(os.path.join(output_dir, "index.rst"), "w") as index_file:
        index_file.write("""\
{title}

The main Pimlico command-line interface (usually accessed via `pimlico.sh` in your project root)
provides subcommands to perform different operations.

For a reference for each command's options, see the command-line documentation: `pimlico.sh --help`, for
a general reference and `pimlico.sh <config_file> <command> --help` for a specific subcommand's
reference.

Below is a more detailed guide for each subcommand (or at least the same reference, if no more detailed
information is available).

.. toctree::
   :maxdepth: 2
   :titlesonly:

   {list}
""".format(
            title=format_heading(0, "Pimlico subcommands"),
            list="\n   ".join(commands),
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate command documentation RST files from core Pimlico "
                                                 "command-line commands")
    parser.add_argument("output_dir", help="Where to put the .rst files")
    opts = parser.parse_args()

    output_dir = os.path.abspath(opts.output_dir)

    # Install basic Pimlico requirements
    install_core_dependencies()

    print "Sphinx %s" % __version__
    print "Pimlico command doc generator"
    print "Outputting module docs to %s" % output_dir

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    generate_docs(output_dir)
