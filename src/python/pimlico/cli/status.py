# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.utils.format import title_box
from termcolor import colored


def module_status_color(module):
    if module.is_filter():
        return "green"
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


def status_cmd(pipeline, opts):
    # Main is the default pipeline config and is always available (but not included in this list)
    variants = ["main"] + pipeline.available_variants
    print "Available pipeline variants: %s" % ", ".join(variants)
    print "Showing status for '%s' variant" % pipeline.variant

    if opts.module_name is None:
        # Try deriving a schedule and output it, including basic status info for each module
        print "\nModule execution schedule with statuses:"
        for i, module_name in enumerate(pipeline.get_module_schedule(), start=1):
            module = pipeline[module_name]
            print colored(status_colored(module, " %d. %s" % (i, module_name)))
            # Check module status (has it been run?)
            print "       status: %s" % status_colored(module, module.status)
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
        to_output = [opts.module_name]
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
        corpus_dir = output_datatype.absolute_base_dir or "not available yet"
        output_info = """\
Output {output_name}:
    {status}
    Datatype: {output_datatype.datatype_name}
    Stored in: {corpus_dir}""".format(
            output_name=output_name,
            status=colored("Data available", "green") if output_datatype.data_ready() else colored("Data not available", "red"),
            output_datatype=output_datatype,
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
{inputs}
{outputs}{lock_status}
Options:
    {options}{module_details}""".format(
        title=colored(title_box("Module: %s" % module.module_name), status_color),
        status=colored("not executable", "green") if module.is_filter() else colored(module.status, status_color),
        inputs="\n".join(input_infos) if input_infos else "No inputs",
        outputs="\n".join(output_infos) if output_infos else "No outputs",
        options="\n    ".join("%s: %s" % (key, val) for (key, val) in module.options.items()),
        module_details=module_details,
        lock_status="" if not module.is_locked() else "\nLocked: ongoing execution",
        docstring=docstring,
    ), also_output
