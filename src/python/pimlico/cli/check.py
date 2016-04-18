from pimlico.core.config import check_pipeline, PipelineCheckError, print_missing_dependencies


def check_cmd(pipeline, opts):
    # Metadata has already been loaded if we've got this far
    print "All module metadata loaded successfully"

    # Output what variants are available and say which we're checking
    print "Available pipeline variants: %s" % ", ".join(["main"] + pipeline.available_variants)
    print "Checking variant '%s'\n" % pipeline.variant

    try:
        check_pipeline(pipeline)
    except PipelineCheckError, e:
        print "Error in pipeline: %s" % e

    if opts.modules:
        passed = print_missing_dependencies(pipeline, opts.modules)
        if passed:
            print "Runtime dependency checks successful for modules: %s" % ", ".join(opts.modules)
