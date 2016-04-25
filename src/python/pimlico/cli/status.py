from pimlico.utils.format import title_box


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
            print " %d. %s" % (i, module_name)
            # Check module status (has it been run?)
            print "       status: %s" % module.status
            # Check status of each input datatypes
            for input_name in module.input_names:
                print "       input %s: %s" % (input_name, "ready" if module.input_ready(input_name) else "not ready")
            print "       outputs: %s" % ", ".join(module.output_names)
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
                already_output.append(module_name)
                # Allow this module to request that we output further modules
                to_output.extend(more_outputs)


def module_status(module):
    also_output = []

    # Put together information about the inputs
    input_infos = []
    for input_name in module.input_names:
        input_module, input_module_output = module.get_input_module_connection(input_name)
        input_datatype = module.get_input(input_name)
        corpus_dir = input_datatype.absolute_base_dir or "not available yet"
        # Format all the information about this input
        input_info = """\
Input {input_name}:
    {status}
    From module: {input_module} ({input_module_output} output)
    Datatype: {input_datatype.datatype_name}""".format(
            input_name=input_name,
            status="Data ready" if module.input_ready(input_name) else "Data not ready",
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
        output_infos.append("""\
Output {output_name}:
    {status}
    Datatype: {output_datatype.datatype_name}
    Stored in: {corpus_dir}""".format(
            output_name=output_name,
            status="Data available" if output_datatype.data_ready() else "Data not available",
            output_datatype=output_datatype,
            corpus_dir=corpus_dir,
        ))

    # Get additional detailed information from the module instance
    module_details = module.get_detailed_status()
    module_details = "\n%s" % "\n".join(module_details) if module_details else ""

    # Put together a neat summary, include the things we've formatted above
    return """
{title}
Status: {status}
{inputs}
{outputs}{module_details}""".format(
        title=title_box("Module: %s" % module.module_name),
        status="not executable" if module.is_filter() else module.status,
        inputs="\n".join(input_infos) if input_infos else "No inputs",
        outputs="\n".join(output_infos) if output_infos else "No outputs",
        module_details=module_details,
    ), also_output
