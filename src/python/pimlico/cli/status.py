# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function
from builtins import map
from builtins import zip

import os
from itertools import cycle
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
        parser.add_argument("--no-sections", "--ns", action="store_true",
                            help="Don't show section headings, but just a list of all the modules")
        parser.add_argument("--expand-all", "--xa", action="store_true",
                            help="Show section headings, expanding all")
        parser.add_argument("--expand", "-x", nargs="*",
                            help="Expand this section number. May be used multiple times. Give a section number "
                                 "like '1.2.3'. To expand the full subtree, give '1.2.3.'")

    def run_command(self, pipeline, opts):
        # If the colour output has been disabled by a switch, use the standard env var to disable it
        if opts.no_color:
            os.environ["ANSI_COLORS_DISABLED"] = "1"
        # Use colorama to control termcolor so that it only outputs colours to the terminal
        colorama.init()
        try:
            # Main is the default pipeline config and is always available (but not included in this list)
            variants = ["main"] + pipeline.available_variants
            print("Available pipeline variants: %s" % ", ".join(variants))
            print("Showing status for '%s' variant" % pipeline.variant)

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
                elif module_sel in pipeline.expanded_modules:
                    # If an expanded module's base name is specified, treat it as a range covering all the modules
                    first_module = pipeline.expanded_modules[module_sel][0]
                    last_module = pipeline.expanded_modules[module_sel][-1]
                    module_sel = None

            if module_sel is None:
                # Try deriving a schedule and output it, including basic status info for each module
                available_module_names = pipeline.modules
                showing_all_modules = True
                if opts.all:
                    # Show all modules, not just those that can be executed
                    print("\nAll modules in pipeline with statuses:")
                    module_names = list(pipeline.modules)
                    bullets = ["-"]*len(module_names)
                else:
                    module_names = [("%d." % i, module) for i, module in enumerate(pipeline.get_module_schedule(), start=1)]

                    if len(module_names) == 0:
                        print("\nPipeline loaded successfully, but it does not contain any modules")
                        return

                    # If the --deps-of option is given, filter modules shown to only those that lead to the given one
                    if opts.deps_of is not None:
                        showing_all_modules = False
                        dest_module = module_number_to_name(pipeline, opts.deps_of)
                        print("\nRestricting status view to dependencies of module '%s'" % dest_module)
                        # Check through the pipeline to find all dependent modules
                        include_mods = [dest_module] + pipeline[dest_module].get_transitive_dependencies()
                        module_names = [(title, module) for (title, module) in module_names if module in include_mods]
                        bullets, module_names = list(zip(*module_names))
                    else:
                        bullets, module_names = list(zip(*module_names))

                        # Fall back to "all" mode if a specific module has been requested that's not in execution schedule
                        if (first_module is not None and first_module not in module_names and first_module in available_module_names) \
                                or (last_module is not None and last_module not in module_names and last_module in available_module_names):
                            module_names = list(pipeline.modules)
                            bullets = ["-"]*len(module_names)
                        else:
                            print("\nModule execution schedule with statuses:")

                # Allow the range of modules to be filtered
                if first_module is not None:
                    # Start at the given module
                    showing_all_modules = False
                    try:
                        first_mod_idx = module_names.index(first_module)
                    except ValueError:
                        raise ValueError("tried to limit module list by '%s': no such module" % first_module)
                    bullets = bullets[first_mod_idx:]
                    module_names = module_names[first_mod_idx:]

                if last_module is not None and last_module not in map(itemgetter(1), module_names):
                    # End at the given module
                    showing_all_modules = False
                    try:
                        last_mod_idx = module_names.index(last_module)
                    except ValueError:
                        raise ValueError("tried to limit module list by '%s': no such module" % last_module)
                    bullets = bullets[:last_mod_idx+1]
                    module_names = module_names[:last_mod_idx+1]

                if opts.short:
                    # Show super-short version of the status
                    # Group module names by status
                    status_lists = {}
                    for bullet, module_name in zip(bullets, module_names):
                        module = pipeline[module_name]
                        # Add this module to the list for its status
                        status_lists.setdefault(module.status, []).append("%s %s" % (bullet, module_name))

                    for status in sorted(status_lists):
                        print("\n%s:" % status)
                        print("\n".join(status_lists[status]))
                else:
                    if not pipeline.has_sections or not opts.no_sections or len(module_names) < 2:
                        # Show with the structure of section headings
                        mod_name_bullets = dict(zip(module_names, bullets))
                        selected_subtree = pipeline.section_headings.subtree(module_names)
                        # If we're showing only a selection of modules, expand the full section heading tree
                        if showing_all_modules:
                            # Only expand requested branches
                            if opts.expand is None:
                                expand = []
                            else:
                                # Use -1 to indicate expansion of the full subtree
                                expand = [tuple([int(n) if len(n) else -1 for n in section.split(".")]) for section in opts.expand]
                                # Also expand the headings above
                                expand = [
                                    sect_num[:i] for sect_num in expand for i in range(1, len(sect_num)+1)
                                ]
                        else:
                            expand = "all"

                        print_section_tree(selected_subtree, mod_name_bullets, pipeline, expand=expand)
                    else:
                        for bullet, module_name in zip(bullets, module_names):
                            # Short summary for each module
                            print_module_status(module_name, bullet, pipeline)
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
                        print(status)
                        if opts.history:
                            # Also output full execution history
                            print("\nFull execution history:")
                            print(module.execution_history)
                        already_output.append(module_name)
                        # Allow this module to request that we output further modules
                        to_output.extend(more_outputs)
        finally:
            colorama.deinit()


def print_section_tree(tree, mod_name_bullets, pipeline, depth=0, expand="all"):
    # Work out whether there will be hidden content
    title_suffix = ""
    expand_all_subtree = expand != "all" and any(x[-1] == -1 and tree.number == x[:-1] for x in expand)
    if expand_all_subtree or tree.name == "root" or expand == "all" or any(tree.number == x for x in expand):
        expanding = True
    else:
        expanding = False
        # If there's more that we're not expanding, indicate this
        if len(tree.modules) or len(tree.subsections):
            title_suffix = " -> ..."

    if tree.name != "root":
        # Don't show the root
        # Work out an appropriate status color for the section
        section_colors = [module_status_color(pipeline[mod]) for mod in tree.subtree_modules()]
        # Apply consistent sorting
        section_colors.sort()
        print("{}{}".format(
            mix_bg_colors("{} {}. {} ".format("#"*depth, tree.number_str(), tree.name), section_colors),
            title_suffix
        ))

    if expanding:
        for module_name in tree.modules:
            # Show the status of each module in the subtree
            print_module_status(module_name, mod_name_bullets[module_name], pipeline)

        for subtree in tree.subsections:
            print_section_tree(subtree, mod_name_bullets, pipeline, depth=depth+1, expand="all" if expand_all_subtree else expand)


def print_module_status(module_name, bullet, pipeline):
    # Short summary for each module
    module = pipeline[module_name]
    print(colored(status_colored(module, " %s %s" % (bullet, module_name))))
    # Show the type of the module
    print("       type: %s" % module.module_type_name)
    # Check module status (has it been run?)
    print("       status: %s" % status_colored(module, module.status if module.module_executable else "not executable"))
    # Check status of each input datatypes
    for input_name in module.input_names:
        print("       input %s: %s" % (
            input_name,
            colored("ready", "green") if module.input_ready(input_name) else colored("not ready", "red")
        ))
    print("       outputs: %s" % ", ".join([
        colored(name, "green") if module.get_output_reader_setup(name).ready_to_read() else colored(name, "red")
        for name in module.output_names
    ]))
    if module.is_locked():
        print("       locked: ongoing execution")


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


_mixing_color_order = ["green", "yellow", "cyan", "red"]
_mixing_fg_colors = ["magenta", "blue", "red", "blue"]


def mix_bg_colors(text, colors):
    """
    Format a string with mixed colors, by alternating by character.
    """
    if len(colors) == 0:
        color_repeats = [None for __ in text]
    else:
        # Proportions for green, yellow, cyan, red
        color_proportions = [
            colors.count("green") / len(colors),
            colors.count("yellow") / len(colors),
            colors.count("cyan") / len(colors),
            colors.count("red") / len(colors),
        ]
        if sum(color_proportions) == 0:
            color_proportions[0] = 1.
        color_repeats = sum(
            ([(fg_col, bg_col)]*int(cp * len(text))
                for (fg_col, bg_col, cp) in zip(_mixing_fg_colors, _mixing_color_order, color_proportions)),
            []
        )
        # Just in case of rounding problems
        while len(color_repeats) < len(text):
            color_repeats.append(color_repeats[-1])
    return "".join(colored(char, color=fg_color, on_color="on_{}".format(bg_color) if bg_color is not None else None)
                   for (char, (fg_color, bg_color)) in zip(text, color_repeats))


def module_status(module):
    """
    Detailed module status, shown when a specific module's status is requested.

    """
    also_output = []
    status_color = module_status_color(module)

    # Put together information about the inputs
    input_infos = []
    for input_name in module.input_names:
        for (input_setup, (input_module, input_module_output)) in \
                zip(module.get_input_reader_setup(input_name, always_list=True),
                    module.get_input_module_connection(input_name, always_list=True)):
            input_datatype = input_setup.datatype
            input_ready = input_setup.ready_to_read()
            # Format all the information about this input
            input_info = """\
Input {input_name}:
    {status}
    From module: {input_module} ({input_module_output} output)
    Datatype: {datatype_name}""".format(
                input_name=input_name,
                status=colored("Data ready", "green") if input_ready else colored("Data not ready", "red"),
                input_module=input_module.module_name,
                input_module_output=input_module_output or "default",
                datatype_name=input_datatype.full_datatype_name(),
            )
            if input_module.module_executable:
                # Executable module: if it's been executed, we get data from there
                input_info += "\n    Executable module"
            elif input_module.is_filter():
                input_info += "\n    Filter module"
            else:
                # Input module
                input_info += "\n    Pipeline input"
            if input_ready:
                # Get the input reader and any additional information it supplies
                input_reader = input_setup(module.pipeline, module=input_module.module_name)
                # Get additional detailed information from the reader
                datatype_details = input_reader.get_detailed_status()
                if datatype_details:
                    input_info += "".join("\n    {}".format(line) for line in datatype_details)
            input_infos.append(input_info)

            # If filter module: output further information about where it gets its inputs from
            if module.is_filter():
                also_output.append(input_module.module_name)

    # Do the same thing for the outputs
    output_infos = []
    for output_name in module.output_names:
        output_setup = module.get_output_reader_setup(output_name)
        output_datatype = output_setup.datatype
        output_ready = output_setup.ready_to_read()
        output_info = """\
Output {output_name}:
    {status}
    Datatype: {output_datatype}{filter_info}""".format(
            output_name=output_name,
            status=colored("Data available", "green") if output_ready else colored("Data not available", "red"),
            output_datatype=output_datatype.full_datatype_name(),
            filter_info="\n    Filter module" if module.is_filter() else "",
        )
        if output_ready:
            # Get additional detailed information from the reader instance
            output_reader = output_setup(module.pipeline, module=module.module_name)
            datatype_details = output_reader.get_detailed_status()
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
    {options}
Module variables:
    {modvars}{module_details}""".format(
        title=colored(title_box("Module: %s" % module.module_name), status_color),
        status=colored("not executable", "green") if not module.module_executable else colored(module.status, status_color),
        inputs="\n".join(input_infos) if input_infos else "No inputs",
        outputs="\n".join(output_infos) if output_infos else "No outputs",
        options="\n    ".join("%s: %s" % (key, val) for (key, val) in module.options.items()),
        module_details=module_details,
        lock_status="" if not module.is_locked() else "\nLocked: ongoing execution",
        docstring=docstring,
        type="%s -- %s" % (module.module_type_name, module.module_readable_name)
                if module.module_readable_name else module.module_type_name,
        modvars="\n    ".join("%s: %s" % (var, val) for (var, val) in module.module_variables.items())
    ), also_output
