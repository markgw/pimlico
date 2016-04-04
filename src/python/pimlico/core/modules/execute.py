import os
import shutil
from pimlico.core.modules.base import DependencyError, load_module_executor
from pimlico.utils.logging import get_console_logger


def execute_module(pipeline, module_name, force_rerun=False, debug=False):
    # Prepare a logger
    log = get_console_logger("Pimlico", debug=debug)

    pipeline_name = "'%s'" % pipeline.name if pipeline.variant == "main" else \
        "'%s' (variant '%s')" % (pipeline.name, pipeline.variant)
    log.info("Loaded pipeline %s" % pipeline_name)

    # Load the module instance
    if module_name not in pipeline.modules:
        raise ModuleExecutionError("%s pipeline doesn't have a module called '%s'" % (pipeline.name, module_name))
    module = pipeline[module_name]
    log.info("Checking module config")
    # Run basic checks on the config for this module
    module.typecheck_inputs()
    # Run checks for runtime dependencies of this module
    missing_dependencies = module.check_runtime_dependencies()
    if len(missing_dependencies):
        raise DependencyError("runtime dependencies not satisfied for executing module '%s':\n%s" % (
            module_name,
            "\n".join("%s for %s (%s)" % (name, module, desc) for (name, module, desc) in missing_dependencies)
        ))

    # Check that previous modules have been completed and input data is ready for us to use
    log.info("Checking inputs")
    for input_name in module.input_names:
        if not module.input_ready(input_name):
            raise ModuleNotReadyError("cannot execute module '%s', since its input '%s' is not ready" %
                                      (module_name, input_name))

    # Check the status of the module, so we don't accidentally overwrite module output that's already complete
    if module.status == "COMPLETE":
        if force_rerun:
            log.info("module '%s' already fully run, but forcing rerun" % module_name)
            # If rerunning, delete the old data first so we make a fresh start
            if os.path.exists(module.get_module_output_dir()):
                shutil.rmtree(module.get_module_output_dir())
        else:
            raise ModuleAlreadyCompletedError("module '%s' has already been run to completion. Use --force-rerun if "
                                              "you want to run it again and overwrite the output" % module_name)
    elif module.status != "UNEXECUTED":
        log.warn("module '%s' has been partially completed before and left with status '%s'. Starting execution again" %
                 (module_name, module.status))

    # Get hold of an executor for this module
    executer = load_module_executor(module)
    # Give the module an initial in-progress status
    module.status = "STARTED"
    executer(module).execute()

    # Update the module status so we know it's been completed
    module.status = "COMPLETE"

    # Tell the user where we put the output
    for output_name in module.output_names:
        output = module.get_output(output_name)
        if output.base_dir is not None:
            log.info("Output '%s' in %s" % (output_name, output.base_dir))


class ModuleExecutionError(Exception):
    pass


class ModuleNotReadyError(ModuleExecutionError):
    pass


class ModuleAlreadyCompletedError(ModuleExecutionError):
    pass


class StopProcessing(Exception):
    pass
