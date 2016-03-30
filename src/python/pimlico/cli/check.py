import sys

from pimlico.core.config import check_for_cycles, PipelineStructureError
from pimlico.utils.format import multiline_tablate


def check_cmd(pipeline, opts):
    # Metadata has already been loaded if we've got this far
    print "All module metadata loaded successfully"

    # Output what variants are available and say which we're checking
    print "Available pipeline variants: %s" % ", ".join(["main"] + pipeline.available_variants)
    print "Checking variant '%s'\n" % pipeline.variant

    # Check the pipeline for cycles
    # This will raise an exception if a cycle is found
    try:
        check_for_cycles(pipeline)
    except PipelineStructureError, e:
        print "Cycle check failed: %s" % e
        sys.exit(1)
    print "No cycles found"

    # Check the types of all the output->input connections
    try:
        for module in pipeline.modules:
            mod = pipeline[module]
            mod.typecheck_inputs()
    except PipelineStructureError, e:
        print "Input typechecking failed: %s" % e
        sys.exit(1)
    print "All inputs pass type checks"

    # Try deriving a schedule
    print "\nModule execution schedule"
    for i, module_name in enumerate(pipeline.get_module_schedule(), start=1):
        print " %d. %s" % (i, module_name)

    if opts.runtime:
        # Also do all runtime checks
        missing_dependencies = []
        for module_name in pipeline.modules:
            missing_dependencies.extend(pipeline[module_name].check_runtime_dependencies())

        if len(missing_dependencies):
            print "\nRuntime dependencies not satisfied:\n%s" % \
                  multiline_tablate(missing_dependencies, [30, 30, 60],
                                    tablefmt="orgtbl", headers=["Dependency", "Module", "Description"])
        else:
            print "\nRuntime dependencies all satisfied"
