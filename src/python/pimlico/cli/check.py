# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from textwrap import wrap

from pimlico.core.config import check_pipeline, PipelineCheckError, print_missing_dependencies, get_dependencies
from pimlico.core.dependencies.base import check_and_install


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
        if "all" in opts.modules:
            # Check all modules
            modules = pipeline.modules
        else:
            modules = pipeline.modules
        passed = print_missing_dependencies(pipeline, modules)
        
        if passed:
            for module_name in modules:
                # Check for remaining execution barriers
                problems = pipeline[module_name].check_ready_to_run()
                if len(problems):
                    for problem_name, problem_desc in problems:
                        print "Module '%s' cannot run: %s\n  %s" % \
                              (module_name, problem_name, "\n  ".join(wrap(problem_desc, 100)))
                    passed = False
            if passed:
                print "Runtime dependency checks successful for modules: %s" % ", ".join(modules)


def install_cmd(pipeline, opts):
    """
    Install missing dependencies.

    """
    try:
        check_pipeline(pipeline)
    except PipelineCheckError, e:
        print "Error in basic pipeline checks, can't proceed to dependency installation until this is fixed: %s" % e
        return

    deps = get_dependencies(pipeline, opts.modules)
    check_and_install(deps, trust_downloaded_archives=opts.trust_downloaded)
