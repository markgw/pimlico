# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""Runtime execution of modules

This module provides the functionality to check that Pimlico modules are ready to execute and execute them.
It is used by the `run` command.

"""
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import str

import os
import socket
import sys

from io import StringIO
from tarfile import TarFile
from textwrap import wrap
from traceback import format_exc, format_tb

from datetime import datetime

from pimlico.cli.util import format_execution_error
from pimlico.core.config import check_pipeline, PipelineCheckError, print_missing_dependencies
from pimlico.core.modules.base import ModuleInfoLoadError, collect_unexecuted_dependencies
from pimlico.core.modules.multistage import MultistageModuleInfo
from pimlico.utils.email import send_pimlico_email
from pimlico.utils.logging import get_console_logger


def check_and_execute_modules(pipeline, module_names, force_rerun=False, debug=False, log=None, all_deps=False,
                              check_only=False, exit_on_error=False, preliminary=False, email=None):
    """
    Main method called by the `run` command that first checks a pipeline, checks all pre-execution requirements
    of the modules to be executed and then executes each of them. The most common case is to execute just one
    module, but a sequence may be given.

    :param exit_on_error: drop out if a ModuleExecutionError occurs in any individual module, instead of continuing
        to the next module that can be run
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
    except PipelineCheckError as e:
        raise ModuleExecutionError("error in pipeline config: %s" % e)

    # Load all the modules from the pipeline
    modules = []
    for module_name in module_names:
        try:
            # Load the module instance
            try:
                module = pipeline[module_name]
            except KeyError as e:
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
        except Exception as e:
            # Intercept all exceptions to add the name of the module that they came from
            e.module_name = module_name
            # Reraise the exception to be caught higher up
            raise

    if all_deps:
        # For each module requested, also include any unexecuted dependencies recursively as far back as necessary
        requested_modules = [m.module_name for m in modules]
        modules = collect_unexecuted_dependencies(modules)
        if len(modules) > len(requested_modules):
            # Report which modules we added
            log.info("Added unexecuted dependent modules to the execution list: %s" % ", ".join(
                m.module_name for m in modules if m.module_name not in requested_modules
            ))

    if not force_rerun:
        # Check the status of the module, so as not to rerun already complete modules
        # By checking this now (even though there's also a check for it in execute_modules), we can remove it
        # from the list at this stage, saving on verbose output later on
        complete_modules = [
            module.module_name for module in modules if module.status == "COMPLETE"
        ]
        if complete_modules:
            log.warning("Removing modules already run to completion: %s" % ", ".join(complete_modules))
            log.info("Use --force-rerun if you want to run modules again and overwrite their output")
            # Remove from the execution list
            modules = [m for m in modules if m.module_name not in complete_modules]
            # This might leave us with no modules to run
            if len(modules) == 0:
                log.warning("No modules left to run!")
                return

    # Check that the module is ready to run
    # If anything fails, an exception is raised
    preliminary_ignored_problems = check_modules_ready(pipeline, modules, log, preliminary=preliminary)
    # Set preliminary only if requested and there were problems that would have prevented running otherwise
    # If preliminary is set by the user, but all inputs are ready anyway, we unset it here
    execute_preliminary = preliminary and len(preliminary_ignored_problems) > 0

    if check_only:
        log.info("All checks passed")
    else:
        # Checks passed: run the module
        # Returns the exit status the should be used (i.e. 1 if there was an error)
        return execute_modules(pipeline, modules, log, force_rerun=force_rerun, debug=debug, exit_on_error=exit_on_error,
                               preliminary=execute_preliminary, email=email)


def check_modules_ready(pipeline, modules, log, preliminary=False):
    """
    Check that a module is ready to be executed. Always called before execution begins.

    :param pipeline: loaded PipelineConfig
    :param modules: loaded ModuleInfo instances, given in the order they're going to be executed.
        For each module, it's assumed that those before it in the list have already been run when it is run.
    :param log: logger to output to
    :return: If `preliminary=True`, list of problems that were ignored by allowing preliminary run. Otherwise,
        None -- we raise an exception when we first encounter a problem
    """
    already_run = []
    non_prelim_missing_inputs = []
    log.info("Checking dependencies and inputs for module%s: %s" %
             ("s" if len(modules) > 1 else "", ", ".join(m.module_name for m in modules)))

    for module in modules:
        module_name = module.module_name

        try:
            # Run checks for runtime dependencies of this module and any others that will be run
            dep_checks_passed = print_missing_dependencies(pipeline, [module_name])
            if not dep_checks_passed:
                raise ModuleExecutionError("runtime dependencies not satisfied for executing module '%s'" %
                                           module_name)

            # Run additional checks the module defines
            problems = module.check_ready_to_run()
            if len(problems):
                for problem_name, problem_desc in problems:
                    print("Module '%s' cannot run: %s\n  %s" % \
                          (module_name, problem_name, "\n  ".join(wrap(problem_desc, 100).splitlines())))
                    raise ModuleExecutionError("runtime checks failed for module '%s'" % module_name)

            # Check that previous modules have been completed and input data is ready for us to use
            missing_inputs = module.missing_data(assume_executed=already_run, allow_preliminary=preliminary)
            if missing_inputs:
                extra_message = ". Assuming %s already run" % ", ".join(already_run) if already_run else ""
                raise ModuleNotReadyError("cannot execute module '%s', since its inputs are not all ready: %s%s" %
                                          (module_name, ", ".join(missing_inputs), extra_message))

            if preliminary:
                # If we've passed the checks while doing a preliminary run, check whether we'd have passed them
                # under normal circumstances
                non_prelim_missing_inputs.extend(module.missing_data(assume_executed=already_run))

            # Check that we're allowed to execute the module
            if module.is_locked():
                raise ModuleExecutionError(
                    "module is locked: is it currently being executed? If not, remove the lock using "
                    "the 'unlock' command")

            # For following modules, assume this one's been run
            already_run.append(module_name)
        except Exception as e:
            # Intercept all exceptions to add the name of the module that they came from
            e.module_name = module_name
            # Reraise the exception to be caught higher up
            raise

    if preliminary:
        return non_prelim_missing_inputs


def execute_modules(pipeline, modules, log, force_rerun=False, debug=False, exit_on_error=False, preliminary=False,
                    email=None):
    # We assume that all checks have been run and that the modules are ready to be executed
    if len(modules) > 1:
        log.info("Executing a sequence of modules: %s" % ", ".join(mod.module_name for mod in modules))
    start_time = datetime.now()

    error_modules = []
    success_modules = []
    skipped_modules = []

    for module in modules:
        module_name = module.module_name
        module_error = False

        if error_modules:
            # Check (again) whether the module's ready
            # If a previous module failed, we might be unable to run this one, even though it passed the checks
            # when we assumed the previous one had been run
            missing_inputs = module.missing_data(assume_failed=error_modules)
            if missing_inputs:
                log.warning("Cannot execute module '%s', since its inputs are not all ready (%s), "
                            "after previous modules failed: %s" %
                            (module_name, ", ".join(missing_inputs), "; ".join(error_modules)))
                error_modules.append(module_name)
                continue

        # Check the status of the module, so we don't accidentally overwrite module output that's already complete
        if module.status == "COMPLETE" and not force_rerun:
            # Don't allow rerunning an already run module, unless --force-rerun was given
            log.warning("module '%s' has already been run to completion. Use --force-rerun if you want to run "
                        "it again and overwrite the output. Rerun not forced, so skipping module" % module_name)
            skipped_modules.append(module_name)
            continue

        # Give some information to the stepper if we're in step mode
        if pipeline.step:
            pipeline._stepper.executing = True

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
                # Should only get here in the case of force rerun
                assert force_rerun
                log.info("module '%s' already fully run, but forcing rerun. If you want to be sure of clearing old "
                         "data, use the 'reset' command" % module_name)
                # We're rerunning, but don't delete old data (i.e. reset module), as there may be something there
                # that the user wants to keep, e.g. caches. They can, of course, reset the module manually if they want
                module.status = "STARTED"
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
            config_store_path = os.path.join(module.get_module_output_dir(absolute=True), "pipeline_config.tar")
            run_num = 1
            while os.path.exists(config_store_path):
                config_store_path = os.path.join(module.get_module_output_dir(absolute=True),
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
                    executor = module.load_executor()
                    try:
                        # Give the module an initial in-progress status
                        end_status = executor(module, debug=debug, force_rerun=force_rerun).execute()
                    except Exception as e:
                        # Catch all exceptions that occur within the executor and wrap them in a ModuleExecutionError
                        # so they can be nicely handled by the error reporting below
                        # Ideally, most expected exceptions will be one of these two types anyway, but of course
                        # unexpected things can go wrong!
                        #
                        # Get traceback for the exception currently being handled
                        # Include the formatted traceback as debugging info for the reraised exception
                        debugging_info = "Uncaught exception in executor. Traceback from original exception: \n%s" % \
                                         "".join(format_tb(sys.exc_info()[2]))
                        raise ModuleExecutionError(str(e), cause=e, debugging_info=debugging_info)
                except (ModuleInfoLoadError, ModuleExecutionError) as e:
                    if type(e) is ModuleExecutionError:
                        # If there's any error, note in the history that execution didn't complete
                        module.add_execution_history_record("Error executing %s: %s" % (module_name, e))
                        log.error("Error executing module '%s': %s" % (module_name, e))
                        # Allow a different end status to be passed up in the exception
                        # If the exception origin didn't specify anything, we just say the module failed
                        end_status = e.end_status or "FAILED"
                    else:
                        module.add_execution_history_record("Error loading %s for execution: %s" % (module_name, e))
                        log.error("Error loading %s for execution: %s" % (module_name, e))
                        # If the module didn't even load, use unstarted status
                        end_status = "UNEXECUTED"

                    debug_mess = StringIO()
                    print("Top-level error", file=debug_mess)
                    print("---------------", file=debug_mess)
                    print(str(format_exc()), file=debug_mess)
                    print(format_execution_error(e), file=debug_mess)
                    debug_mess = debug_mess.getvalue()

                    # Put the whole error info into a file so we can see what went wrong
                    error_filename = module.get_new_log_filename()
                    with open(error_filename, "w") as error_file:
                        error_file.write(debug_mess)

                    if debug or exit_on_error:
                        # In debug mode, also output the full info to the terminal
                        # Do this also if we're dropping out after encountering an error
                        print(debug_mess, file=sys.stderr)
                    else:
                        log.error("Full debug info output to %s" % error_filename)

                    # Only send email error report if this was an execution error, not a load error
                    if type(e) is ModuleExecutionError and email == "modend":
                        # Finer-grained email notifications have been requested
                        # Send an error report now
                        send_module_report_email(pipeline, module, str(e), debug_mess)

                    module.add_execution_history_record("Debugging output in %s" % error_filename)
                    module_error = True
                except KeyboardInterrupt:
                    module.add_execution_history_record("Execution of %s halted by user" % module_name)
                    raise
            finally:
                # Always remove the lock at the end, even if something goes wrong
                module.unlock()

            if end_status is None or end_status == "COMPLETE":
                # Update the module status so we know it's been completed
                if preliminary:
                    # Don't set status to COMPLETE if we were just doing a preliminary run, to avoid confusion
                    module.status = "COMPLETE_PRELIMINARY"
                    module.add_execution_history_record("Preliminary exectuion complete")
                else:
                    module.status = "COMPLETE"
                    module.add_execution_history_record("Execution completed successfully")
            else:
                # Custom status was given
                module.status = end_status
                module.add_execution_history_record("Execution completed with status %s" % end_status)
        except Exception as e:
            # Intercept all exceptions to add the name of the module that they came from
            e.module_name = module_name
            module.add_execution_history_record("Execution interruption by %s exception" % type(e).__name__)
            # Reraise the exception to be caught higher up
            raise

        if module_error:
            # Module failed in one way or another
            error_modules.append(module_name)
            if exit_on_error:
                # Don't carry on to the next module
                break
        else:
            success_modules.append(module_name)

    # Notify the stepper (if we're debugging) that we're not executing any more
    if pipeline.step:
        pipeline._stepper.executing = False

    # Output a summary of what we succeeded and failed on
    if error_modules:
        if success_modules:
            log.error("Execution failed on %d modules: %s" % (len(error_modules), ", ".join(error_modules)))
            log.info("Execution succeeded on %d modules: %s" % (len(success_modules), ", ".join(success_modules)))
        elif len(error_modules) == 1:
            log.error("Execution of %s failed" % error_modules[0])
        else:
            log.error("Execution failed on all modules (%s)" % ", ".join(error_modules))
    else:
        log.info("Successfully executed all modules: %s" % ", ".join(success_modules))
    if skipped_modules:
        log.info("Skipped modules: %s" % ", ".join(skipped_modules))

    if email:
        # If we're emailing a status report, do so now
        # Don't do this if only a few seconds have passed since we started: i.e. something went wrong straight away
        if (datetime.now() - start_time).total_seconds() > 20.:
            send_final_report_email(pipeline, error_modules, success_modules, skipped_modules, modules)
        else:
            log.warn("Not sending email, since we failed so quickly")

    if error_modules:
        return 1
    else:
        return 0


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


def send_final_report_email(pipeline, error_modules, success_modules, skipped_modules, all_modules):
    subject = "[Pimlico] Execution of '%s' completed: final report" % pipeline.name

    # Put together a report
    lines = [
        "Pimlico execution report for pipeline: %s" % pipeline.name,
        "Execution completed at %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Running on %s" % socket.gethostname(),
        "",
        "Execution of modules: %s" % ", ".join(m.module_name for m in all_modules),
        "\n",
    ]
    # Output a summary of what we succeeded and failed on
    # This is very similar to the little report we output to the log at the end of execution
    if error_modules:
        if success_modules:
            lines.append("Execution failed on %d modules: %s" % (len(error_modules), ", ".join(error_modules)))
            lines.append("Execution succeeded on %d modules: %s" % (len(success_modules), ", ".join(success_modules)))
        elif len(error_modules) == 1:
            lines.append("Execution of %s failed" % error_modules[0])
        else:
            lines.append("Execution failed on all modules (%s)" % ", ".join(error_modules))
    else:
        lines.append("Successfully executed all modules:")
        lines.append(", ".join(success_modules))
    if skipped_modules:
        lines.append("Skipped modules: %s" % ", ".join(skipped_modules))

    content = "\n".join(lines)

    # Send email report
    send_pimlico_email(subject, content, pipeline.local_config, pipeline.log)


def send_module_report_email(pipeline, module, short_error, long_error):
    subject = "[Pimlico] Module '%s' failed in pipeline '%s'" % (module.module_name, pipeline.name)

    # Put together a report
    lines = [
        "Pimlico execution report for pipeline: %s" % pipeline.name,
        "Running on %s" % socket.gethostname(),
        "Module '%s' failed at %s" % (module.module_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "",
        "Error: %s" % short_error,
        "\n",
        "Longer error report:",
        # This is the same as what gets logged to a file
        long_error,
    ]

    content = "\n".join(lines)
    # Send email report
    send_pimlico_email(subject, content, pipeline.local_config, pipeline.log)


class ModuleExecutionError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        self.debugging_info = kwargs.pop("debugging_info", None)
        self.end_status = kwargs.pop("end_status", None)
        super(ModuleExecutionError, self).__init__(*args, **kwargs)


class ModuleNotReadyError(ModuleExecutionError):
    pass


class ModuleAlreadyCompletedError(ModuleExecutionError):
    pass


class StopProcessing(Exception):
    pass
