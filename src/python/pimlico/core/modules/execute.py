from pimlico.core.modules.base import DependencyError


def execute_module(pipeline, module_name):
    # Load the module instance
    module = pipeline[module_name]
    # Run basic checks on the config for this module
    module.typecheck_inputs()
    # Run checks for runtime dependencies of this module
    missing_dependencies = module.check_runtime_dependencies()
    if len(missing_dependencies):
        raise DependencyError("runtime dependencies not satisfied for executing module '%s':\n%s" % (
            module_name,
            "\n".join("%s for %s (%s)" % (name, module, desc) for (name, module, desc) in missing_dependencies)
        ))

    # TODO Check that input data is ready, i.e. that previous modules have been run
    # TODO Actually run
