# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
import os
from operator import itemgetter

import colorama
from termcolor import colored

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.cli.util import module_number_to_name
from pimlico.utils.format import title_box


class StatusCmd(PimlicoCLISubcommand):
    command_name = "status"
    command_help = "Output a module execution schedule for the pipeline and execution status for every module"

    def add_arguments(self, parser):
        parser.add_argument("module_name", nargs="?",
                            help="Optionally specify a module name (or number). More detailed status information will "
                                 "be outut for this module. Alternatively, use this arg to limit the modules whose "
                                 "status will be output to a range by specifying 'A...B', where A and B are module "
                                 "names or numbers")
        parser.add_argument("--all", "-a", action="store_true",
                            help="Show all modules defined in the pipeline, not just those that can be executed")
        parser.add_argument("--short", "-s", action="store_true",
                            help="Use a brief format when showing the full pipeline's status. Only applies when "
                                 "module names are not specified. This is useful with very large pipelines, where "
                                 "you just want a compact overview of the status")
        parser.add_argument("--history", "-i", action="store_true",
                            help="When a module name is given, even more detailed output is given, including the full "
                                 "execution history of the module")
        parser.add_argument("--deps-of", "-d",
                            help="Restrict to showing only the named/numbered module and any that are (transitive) "
                                 "dependencies of it. That is, show the whole tree of modules that lead through "
                                 "the pipeline to the given module")
        parser.add_argument("--no-color", "--nc", action="store_true",
                            help="Don't include terminal color characters, even if the terminal appears to support "
                                 "them. This can be useful if the automatic detection of color terminals doesn't work "
                                 "and the status command displays lots of horrible escape characters")

    def run_command(self, pipeline, opts):
        # If the colour output has been disabled by a switch, use the standard env var to disable it
        if opts.no_color:
            os.environ["ANSI_COLORS_DISABLED"] = "1"
        # Use colorama to control termcolor so that it only outputs colours to the terminal
        colorama.init()
        try:
            # Main is the default pipeline config and is always available (but not included in this list)
            variants = ["main"] + pipeline.available_variants
            print "Available pipeline variants: %s" % ", ".join(variants)
            print "Showing status for '%s' variant" % pipeline.variant

            module_sel = opts.module_name
            first_module = last_module = None
            if module_sel is not None:
                if "..." in module_sel:
                    # A module range specifier was given to limit the modules shown
                    first_module, __, last_module = module_sel.partition("...")
                    # Allow module numbers to be given
                    if len(first_module):
                        first_module = module_number_to_name(pipeline, first_module)
                    else:
                        # Start from the very beginning
                        first_module = None
                    if len(last_module):
                        last_module = module_number_to_name(pipeline, last_module)
                    else:
                        # Continue to the end
                        last_module = None
                    # Show the non-detailed version, since we're selecting a range, not just one
                    module_sel = None

            if module_sel is None:
                # Try deriving a schedule and output it, including basic status info for each module
                if opts.all:
                    # Show all modules, not just those that can be executed
                    print "\nAll modules in pipeline with statuses:"
                    module_names = [("-", module) for module in pipeline.modules]
                    module_numbers = [None for x in module_names]
                else:
                    module_names = [("%d." % i, module) for i, module in enumerate(pipeline.get_module_schedule(), start=1)]
                    module_numbers = list(range(1, len(module_names)+1))

                    # If the --deps-of option is given, filter modules shown to only those that lead to the given one
                    if opts.deps_of is not None:
                        dest_module = module_number_to_name(pipeline, opts.deps_of)
                        print "\nRestricting status view to dependencies of module '%s'" % dest_module
                        # Check through the pipeline to find all dependent modules
                        include_mods = [dest_module] + pipeline[dest_module].get_transitive_dependencies()
                        module_names = [(title, module) for (title, module) in module_names if module in include_mods]
                    else:
                        print "\nModule execution schedule with statuses:"
                bullets, module_names = zip(*module_names)

                # Allow the range of modules to be filtered
                if first_module is not None:
                    # Start at the given module
                    try:
                        first_mod_idx = module_names.index(first_module)
                    except ValueError:
                        raise ValueError("no such module in the list limit by: %s" % first_module)
                    bullets = bullets[first_mod_idx:]
                    module_names = module_names[first_mod_idx:]

                if last_module is not None and last_module not in map(itemgetter(1), module_names):
                    # End at the given module
                    try:
                        last_mod_idx = module_names.index(last_module)
                    except ValueError:
                        raise ValueError("no such module in the list limit by: %s" % first_module)
                    bullets = bullets[:last_mod_idx+1]
                    module_names = module_names[:last_mod_idx+1]

                if opts.short:
                    # Show super-short version of the status
                    # Group module names by status
                    status_lists = {}
                    for module_num, module_name in zip(module_numbers, module_names):
                        module = pipeline[module_name]
                        # Only show the bullets if they're module numbers, not just bullets
                        show_name = ("%s (%d)" % (module_name, module_num)) if module_num is not None else module_name
                        # Add this module to the list for its status
                        status_lists.setdefault(module.status, []).append(show_name)

                    for status in sorted(status_lists):
                        print "\n%s:" % status
                        print "\n".join(status_lists[status])
                else:
                    for bullet, module_name in zip(bullets, module_names):
                        module = pipeline[module_name]
                        print colored(status_colored(module, " %s %s" % (bullet, module_name)))
                        # Show the type of the module
                        print "       type: %s" % module.module_type_name
                        # Check module status (has it been run?)
                        print "       status: %s" % status_colored(module, module.status if module.module_executable else "not executable")
                        # Check status of each input datatypes
                        for input_name in module.input_names:
                            print "       input %s: %s" % (
                                input_name,
                                colored("ready", "green") if module.input_ready(input_name) else colored("not ready", "red")
                            )
                        print "       outputs: %s" % ", ".join(module.output_names)
                        if module.is_locked():
                            print "       locked: ongoing execution"
            else:
                # Output more detailed status information for this module
                to_output = [module_sel]
                already_output = []

                while len(to_output):
                    module_name = to_output.pop()
                    if module_name not in already_output:
                        module = pipeline[module_name]
                        status, more_outputs = module_status(module)
                        # Output the module's detailed status
                        print status
                        if opts.history:
                            # Also output full execution history
                            print "\nFull execution history:"
                            print module.execution_history
                        already_output.append(module_name)
                        # Allow this module to request that we output further modules
                        to_output.extend(more_outputs)
        finally:
            colorama.deinit()


def module_status_color(module):
    if not module.module_executable:
        if module.all_inputs_ready():
            return "green"
        else:
            return "red"
    elif module.status == "COMPLETE":
        return "green"
    elif module.status == "UNEXECUTED":
        # If the module's not been started, but its inputs are ready, use yellow
        if module.all_inputs_ready():
            return "yellow"
        else:
            return "red"
    else:
        # All other cases are blue -- usually partial completion, ongoing execution, etc
        return "cyan"


def status_colored(module, text=None):
    """
    Colour the text according to the status of the given module. If text is not given, the module's name is
    returned.

    """
    text = text or module.module_name
    return colored(text, module_status_color(module))


def module_status(module):
    also_output = []
    status_color = module_status_color(module)

    # Put together information about the inputs
    input_infos = []
    for input_name in module.input_names:
        for (input_datatype, (input_module, input_module_output, input_additional_names)) in \
                zip(module.get_input(input_name, always_list=True),
                    module.get_input_module_connection(input_name, always_list=True)):
            corpus_dir = input_datatype.absolute_base_dir or "not available yet"
            # Format all the information about this input
            input_info = """\
Input {input_name}:
    {status}
    From module: {input_module} ({input_module_output} output)
    Datatype: {input_datatype.datatype_name}""".format(
                input_name=input_name,
                status=colored("Data ready", "green") if module.input_ready(input_name) else colored("Data not ready", "red"),
                input_module=input_module.module_name,
                input_module_output=input_module_output or "default",
                input_datatype=input_datatype,
            )
            if input_module.module_executable:
                # Executable module: if it's been executed, we get data from there
                if module.input_ready(input_name):
                    input_info += "\n    Stored in: {corpus_dir}".format(corpus_dir=corpus_dir)
            elif input_module.is_filter():
                # Filter module: output further information about where it gets its inputs from
                input_info += "\n    Input module is a filter"
                also_output.append(input_module.module_name)
            else:
                # Input module
                input_info += "\n    Pipeline input"
            if input_datatype.data_ready():
                # Get additional detailed information from the datatype instance
                datatype_details = input_datatype.get_detailed_status()
                if datatype_details:
                    # Indent the lines
                    input_info = "%s\n%s" % (input_info, "\n".join("    %s" % line for line in datatype_details))
            input_infos.append(input_info)

    # Do the same thing for the outputs
    output_infos = []
    for output_name in module.output_names:
        output_datatype = module.get_output(output_name)
        if module.is_filter():
            corpus_dir = "filter module, output not stored"
        else:
            corpus_dir = output_datatype.absolute_base_dir or "not available yet"
        output_info = """\
Output {output_name}:
    {status}
    Datatype: {output_datatype}
    Stored in: {corpus_dir}""".format(
            output_name=output_name,
            status=colored("Data available", "green") if output_datatype.data_ready() else colored("Data not available", "red"),
            output_datatype=output_datatype.full_datatype_name(),
            corpus_dir=corpus_dir,
        )
        if output_datatype.data_ready():
            # Get additional detailed information from the datatype instance
            datatype_details = output_datatype.get_detailed_status()
            if datatype_details:
                # Indent the lines
                output_info = "%s\n%s" % (output_info, "\n".join("    %s" % line for line in datatype_details))
        output_infos.append(output_info)

    # Get additional detailed information from the module instance
    module_details = module.get_detailed_status()
    module_details = "\n%s" % "\n".join(module_details) if module_details else ""

    if module.docstring:
        docstring = "%s\n" % module.docstring
    else:
        docstring = ""

    # Put together a neat summary, include the things we've formatted above
    return """
{title}
{docstring}Status: {status}
Type: {type}
{inputs}
{outputs}{lock_status}
Options:
    {options}{module_details}""".format(
        title=colored(title_box("Module: %s" % module.module_name), status_color),
        status=colored("not executable", "green") if not module.module_executable else colored(module.status, status_color),
        inputs="\n".join(input_infos) if input_infos else "No inputs",
        outputs="\n".join(output_infos) if output_infos else "No outputs",
        options="\n    ".join("%s: %s" % (key, val) for (key, val) in module.options.items()),
        module_details=module_details,
        lock_status="" if not module.is_locked() else "\nLocked: ongoing execution",
        docstring=docstring,
        type="%s -- %s" % (module.module_type_name, module.module_readable_name)
                if module.module_readable_name else module.module_type_name
    ), also_output
