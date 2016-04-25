import os
from tarfile import TarFile

from pimlico.core.config import check_pipeline, PipelineCheckError, print_missing_dependencies
from pimlico.core.modules.base import load_module_executor
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
    # Run basic checks on the config for the whole pipeline
    try:
        check_pipeline(pipeline)
    except PipelineCheckError, e:
        raise ModuleExecutionError("error in pipeline config: %s" % e)
    # Run checks for runtime dependencies of this module
    dep_checks_passed = print_missing_dependencies(pipeline, [module_name])
    if not dep_checks_passed:
        raise ModuleExecutionError("runtime dependencies not satisfied for executing module '%s'" % module_name)

    # Check that previous modules have been completed and input data is ready for us to use
    log.info("Checking inputs")
    missing_inputs = module.missing_data()
    if missing_inputs:
        raise ModuleNotReadyError("cannot execute module '%s', since its inputs are not all ready: %s" %
                                  (module_name, ", ".join(missing_inputs)))

    # Check the status of the module, so we don't accidentally overwrite module output that's already complete
    if module.status == "COMPLETE":
        if force_rerun:
            log.info("module '%s' already fully run, but forcing rerun" % module_name)
            # If rerunning, delete the old data first so we make a fresh start
            module.reset_execution()
            module.status = "STARTED"
        else:
            raise ModuleAlreadyCompletedError("module '%s' has already been run to completion. Use --force-rerun if "
                                              "you want to run it again and overwrite the output" % module_name)
    elif module.status == "UNEXECUTED":
        # Not done anything on this yet
        module.status = "STARTED"
        module.add_execution_history_record("Starting execution from the beginning")
    else:
        log.warn("module '%s' has been partially completed before and left with status '%s'. Starting executor" %
                 (module_name, module.status))
        module.add_execution_history_record("Starting executor with status '%s'" % module.status)

    # Tell the user where we put the output
    for output_name in module.output_names:
        output_dir = module.get_absolute_output_dir(output_name)
        log.info("Outputting '%s' in %s" % (output_name, output_dir))

    # Store a copy of all the config files from which the pipeline was loaded, so we can see exactly what we did later
    config_store_path = os.path.join(module.get_module_output_dir(short_term_store=True), "pipeline_config.tar")
    run_num = 1
    while os.path.exists(config_store_path):
        config_store_path = os.path.join(module.get_module_output_dir(short_term_store=True), "pipeline_config.%d.tar"
                                         % run_num)
        run_num += 1
    with TarFile(config_store_path, "w") as config_store_tar:
        # There may be multiple config files due to includes: store them all
        # To be able to recreate the pipeline easily, we should store the directory structure relative to the main
        # config, but since this is mainly just for looking at, we just chuck all the files in
        for config_filename in pipeline.all_filenames:
            config_store_tar.add(config_filename, recursive=False)
    module.add_execution_history_record("Storing full pipeline config used to execute %s in %s" %
                                        (module_name, config_store_path))

    try:
        # Get hold of an executor for this module
        executer = load_module_executor(module)
        # Give the module an initial in-progress status
        executer(module).execute()
    except ModuleExecutionError, e:
        # If there's any error, note in the history that execution didn't complete
        module.add_execution_history_record("Error executing %s: %s" % (module_name, e))
        raise
    except KeyboardInterrupt:
        module.add_execution_history_record("Execution of %s halted by user" % module_name)
        raise

    # Update the module status so we know it's been completed
    module.status = "COMPLETE"


class ModuleExecutionError(Exception):
    pass


class ModuleNotReadyError(ModuleExecutionError):
    pass


class ModuleAlreadyCompletedError(ModuleExecutionError):
    pass


class StopProcessing(Exception):
    pass
