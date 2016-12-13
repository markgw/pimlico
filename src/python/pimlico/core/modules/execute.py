# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""Runtime execution of modules

This module provides the functionality to check that Pimlico modules are ready to execute and execute them.
It is used by the `run` command.

"""

import os
from tarfile import TarFile
from textwrap import wrap

from pimlico.core.config import check_pipeline, PipelineCheckError, print_missing_dependencies, PipelineStructureError
from pimlico.core.modules.base import ModuleInfoLoadError, collect_unexecuted_dependencies
from pimlico.core.modules.multistage import MultistageModuleInfo
from pimlico.utils.logging import get_console_logger


def check_and_execute_modules(pipeline, module_names, force_rerun=False, debug=False, log=None, all_deps=False,
                              check_only=False):
    """
    Main method called by the `run` command that first checks a pipeline, checks all pre-execution requirements
    of the modules to be executed and then executes each of them. The most common case is to execute just one
    module, but a sequence may be given.

    :param pipeline: loaded PipelineConfig
    :param module_names: list of names of modules to execute in the order they should be run
    :param force_rerun: execute modules, even if they're already marked as complete
    :param debug: output debugging info
    :param log: logger, if you have one you want to reuse
    :param all_deps: also include unexecuted dependencies of the given modules
    :param check_only: run all checks, but stop before executing. Used for `check` command
    :return:
    """
    if log is None:
        # Prepare a logger
        log = get_console_logger("Pimlico", debug=debug)

    # Run basic checks on the config for the whole pipeline
    try:
        check_pipeline(pipeline)
    except PipelineCheckError, e:
        raise ModuleExecutionError("error in pipeline config: %s" % e)

    # Load all the modules from the pipeline
    modules = []
    for module_name in module_names:
        try:
            # Load the module instance
            try:
                module = pipeline[module_name]
            except KeyError, e:
                raise ModuleExecutionError("could not load module '%s'" % module_name)

            # If we loaded a multi-stage module, default to executing its next unexecuted stage
            if isinstance(module, MultistageModuleInfo):
                module, next_stage = module.get_next_stage()
                if next_stage is None:
                    raise ModuleAlreadyCompletedError("All stages of multi-stage module have been completed")
                else:
                    log.info("Multi-stage module without stage specified: defaulting to next incomplete stage, '%s'" %
                             next_stage.name)

            modules.append(module)
        except Exception, e:
            # Intercept all exceptions to add the name of the module that they came from
            e.module_name = module_name
            # Reraise the exception to be caught higher up
            raise

    if all_deps:
        # For each module requested, also include any unexecuted dependencies recursively as far back as necessary
        requested_modules = [m.module_name for m in modules]
        modules = collect_unexecuted_dependencies(modules)
        if len(modules) > len(requested_modules):
            log.info("Added unexecuted dependent modules to the execution list")
            log.info("Resulting list: %s" % ", ".join(
                # Mark added modules with a *
                ("*" if m.module_name not in requested_modules else "") + m.module_name for m in modules
            ))

    # Check that the module is ready to run
    # If anything fails, an exception is raised
    check_modules_ready(pipeline, modules, log, force_rerun=force_rerun)

    if check_only:
        log.info("All checks passed")
    else:
        # Checks passed: run the module
        execute_modules(pipeline, modules, log, force_rerun=force_rerun, debug=debug)


def check_modules_ready(pipeline, modules, log, force_rerun=False):
    """
    Check that a module is ready to be executed. Always called before execution begins.

    :param pipeline: loaded PipelineConfig
    :param modules: loaded ModuleInfo instances, given in the order they're going to be executed.
        For each module, it's assumed that those before it in the list have already been run when it is run.
    :param log: logger to output to
    :return:
    """
    already_run = []

    for module in modules:
        module_name = module.module_name

        try:
            log.info("Checking dependencies and inputs for module '%s'" % module_name)
            # Run checks for runtime dependencies of this module and any others that will be run
            dep_checks_passed = print_missing_dependencies(pipeline, [module_name])
            if not dep_checks_passed:
                raise ModuleExecutionError("runtime dependencies not satisfied for executing module '%s'" %
                                           module_name)

            # Run additional checks the module defines
            problems = module.check_ready_to_run()
            if len(problems):
                for problem_name, problem_desc in problems:
                    print "Module '%s' cannot run: %s\n  %s" % \
                          (module_name, problem_name, "\n  ".join(wrap(problem_desc, 100).splitlines()))
                    raise ModuleExecutionError("runtime checks failed for module '%s'" % module_name)

            # Check that previous modules have been completed and input data is ready for us to use
            missing_inputs = module.missing_data(assume_executed=already_run)
            if missing_inputs:
                extra_message = ". Assuming %s already run" % ", ".join(already_run) if already_run else ""
                raise ModuleNotReadyError("cannot execute module '%s', since its inputs are not all ready: %s%s" %
                                          (module_name, ", ".join(missing_inputs), extra_message))

            # Check that we're allowed to execute the module
            if module.is_locked():
                raise ModuleExecutionError(
                    "module is locked: is it currently being executed? If not, remove the lock using "
                    "the 'unlock' command")

            # Check the status of the module, so we don't accidentally overwrite module output that's already complete
            if module.status == "COMPLETE":
                # Allow rerunning an already run module
                if not force_rerun:
                    raise ModuleAlreadyCompletedError("module '%s' has already been run to completion. Use --force-rerun "
                                                      "if you want to run it again and overwrite the output" % module_name)

            # For following modules, assume this one's been run
            already_run.append(module_name)
        except Exception, e:
            # Intercept all exceptions to add the name of the module that they came from
            e.module_name = module_name
            # Reraise the exception to be caught higher up
            raise


def execute_modules(pipeline, modules, log, force_rerun=False, debug=False):
    # We assume that all checks have been run and that the modules are ready to be executed
    if len(modules) > 1:
        log.info("Executing a sequence of modules: %s" % ", ".join(mod.module_name for mod in modules))

    for module in modules:
        module_name = module.module_name

        try:
            # If running multiple modules, output something between them so it's clear where they start and end
            if len(modules) > 1:
                mess = "Executing %s" % module_name
                log.info("=" * (len(mess) + 4))
                log.info("| %s |" % mess)
                log.info("=" * (len(mess) + 4))

            log.info("Executing module tree:")
            execution_tree = module.get_execution_dependency_tree()
            for line in format_execution_dependency_tree(execution_tree):
                log.info("  %s" % line)

            # Check the status of the module, so we don't accidentally overwrite module output that's already complete
            if module.status == "COMPLETE":
                if force_rerun:
                    log.info("module '%s' already fully run, but forcing rerun" % module_name)
                    # If rerunning, delete the old data first so we make a fresh start
                    module.reset_execution()
                    module.status = "STARTED"
                else:
                    # Should have been caught by pre-execution checks, but check again
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

            # Store a copy of all the config files from which the pipeline was loaded, so we can see exactly
            # what we did later
            config_store_path = os.path.join(module.get_module_output_dir(short_term_store=True), "pipeline_config.tar")
            run_num = 1
            while os.path.exists(config_store_path):
                config_store_path = os.path.join(module.get_module_output_dir(short_term_store=True),
                                                 "pipeline_config.%d.tar" % run_num)
                run_num += 1
            with TarFile(config_store_path, "w") as config_store_tar:
                # There may be multiple config files due to includes: store them all
                # To be able to recreate the pipeline easily, we should store the directory structure relative to the
                # main config, but since this is mainly just for looking at, we just chuck all the files in
                for config_filename in pipeline.all_filenames:
                    config_store_tar.add(config_filename, recursive=False, arcname=os.path.basename(config_filename))
            module.add_execution_history_record("Storing full pipeline config used to execute %s in %s" %
                                                (module_name, config_store_path))

            try:
                module.lock()

                try:
                    # Get hold of an executor for this module
                    executer = module.load_executor()
                    # Give the module an initial in-progress status
                    end_status = executer(module, debug=debug, force_rerun=force_rerun).execute()
                except ModuleInfoLoadError, e:
                    module.add_execution_history_record("Error loading %s for execution: %s" % (module_name, e))
                    raise
                except ModuleExecutionError, e:
                    # If there's any error, note in the history that execution didn't complete
                    module.add_execution_history_record("Error executing %s: %s" % (module_name, e))
                    raise
                except KeyboardInterrupt:
                    module.add_execution_history_record("Execution of %s halted by user" % module_name)
                    raise
            finally:
                # Always remove the lock at the end, even if something goes wrong
                module.unlock()

            if end_status is None:
                # Update the module status so we know it's been completed
                module.status = "COMPLETE"
            else:
                # Custom status was given
                module.status = end_status
        except Exception, e:
            # Intercept all exceptions to add the name of the module that they came from
            e.module_name = module_name
            # Reraise the exception to be caught higher up
            raise


def format_execution_dependency_tree(tree):
    module, inputs = tree
    lines = ["%s" % module]
    for (input_name, output_name, input_tree) in inputs:
        if output_name is None:
            output_name = "default_output"
        input_lines = format_execution_dependency_tree(input_tree)
        input_lines = ["|- %s.%s" % (input_lines[0], output_name)] + ["|  %s" % line for line in input_lines[1:]]
        lines.extend(input_lines)
    return lines


class ModuleExecutionError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        self.debugging_info = kwargs.pop("debugging_info", None)
        super(ModuleExecutionError, self).__init__(*args, **kwargs)


class ModuleNotReadyError(ModuleExecutionError):
    pass


class ModuleAlreadyCompletedError(ModuleExecutionError):
    pass


class StopProcessing(Exception):
    pass
