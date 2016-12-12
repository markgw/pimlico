from pimlico.utils.core import remove_duplicates


def inputs_cmd(pipeline, opts):
    module_name = opts.module_name
    print "Input locations for module '%s'" % module_name
    module = pipeline[module_name]

    # Display info for each input to this module
    for input_name in module.input_names:
        print "\nInput '%s'" % input_name
        input_lst = module.get_input(input_name, always_list=True)
        input_connections = module.get_input_module_connection(input_name, always_list=True)
        multiple_inputs = len(input_lst) > 1
        if multiple_inputs:
            print "Multiple input sources: showing locations for all"

        for i, (input_datatype, (prev_module, prev_output_name, __)) in \
                enumerate(zip(input_lst, input_connections)):
            if multiple_inputs:
                print "## Input source %d ##" % i

            if input_datatype.data_ready():
                corpus_dir = input_datatype.absolute_base_dir
                if corpus_dir is None:
                    print "Data (%s) available, but no directory given: probably a filter datatype" % \
                          input_datatype.full_datatype_name()
                else:
                    print "Data (%s) available in:" % input_datatype.full_datatype_name()
                    print " - %s" % corpus_dir
            else:
                print "Data not available. Data will be found in any of the following locations:"
                # Get the relative dir within the Pimlico dir structures
                rel_path = prev_module.get_output_dir(prev_output_name)
                # Resolve this to all possible absolute dirs (usually two)
                abs_paths = remove_duplicates(pipeline.get_data_search_paths(rel_path))
                print "\n".join(" - %s" % pth for pth in abs_paths)


def output_cmd(pipeline, opts):
    module_name = opts.module_name
    module = pipeline[module_name]
    # Get the output dir for the module
    module_output_dir = module.get_module_output_dir(short_term_store=True)
    print "Output location for module '%s': %s" % (module_name, module_output_dir)
