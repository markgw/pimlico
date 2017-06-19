import sys
from traceback import print_exc, format_exception_only

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.cli.util import print_execution_error
from pimlico.core.modules.base import ModuleInfoLoadError
from pimlico.core.modules.execute import check_and_execute_modules, ModuleExecutionError, ModuleNotReadyError
from pimlico.core.modules.multistage import MultistageModuleInfo
from pimlico.utils.logging import get_console_logger


class RunCmd(PimlicoCLISubcommand):
    """
    Main command for executing Pimlico modules from the command line `run` command.

    """
    command_name = "run"
    command_help = "Execute an individual pipeline module, or a sequence"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*",
                            help="The name (or number) of the module to run. To run a stage from a multi-stage "
                                 "module, use 'module:stage'. Use 'status' command to see available modules. "
                                 "Use 'module:?' or 'module:help' to list available stages. If not given, "
                                 "defaults to next incomplete module that has all its inputs ready. You may give "
                                 "multiple modules, in which case they will be executed in the order specified")
        parser.add_argument("--force-rerun", "-f", action="store_true",
                            help="Force running the module(s), even if it's already been run to completion")
        parser.add_argument("--all-deps", "-a", action="store_true",
                            help="If the given module(s) has dependent modules that have not been completed, executed "
                                 "them first. This allows you to specify a module late in the pipeline and execute the "
                                 "full pipeline leading to that point")
        parser.add_argument("--dry-run", "--dry", "--check", action="store_true",
                            help="Perform all pre-execution checks, but don't actually run the module(s)")
        parser.add_argument("--step", action="store_true",
                            help="Enabled super-verbose debugging mode, which steps through a module's processing "
                                 "outputting a lot of information and allowing you to control the output as it goes. "
                                 "Useful for working out what's going on inside a module if it's mysteriously not "
                                 "producing the output you expected")
        parser.add_argument("--preliminary", "--pre", action="store_true",
                            help="Perform a preliminary run of any modules that take multiple datasets into one of "
                                 "their inputs. This means that we will run the module even if not all the datasets "
                                 "are yet available (but at least one is) and mark it as preliminarily completed")
        parser.add_argument("--exit-on-error", "-e", action="store_true",
                            help="If an error is encountered while executing a module that causes the whole module "
                                 "execution to fail, output the error and exit. By default, Pimlico will send "
                                 "error output to a file (or print it in debug mode) and continue to execute the "
                                 "next module that can be executed, if any")
        parser.add_argument("--email", choices=["modend", "end"],
                            help="Send email notifications when processing is complete, including information about "
                                 "the outcome. Choose from: 'modend' (send notification after module execution if it "
                                 "fails and a summary at the end of everything), 'end' "
                                 "(send only the final summary). Email sending must be configured: "
                                 "see 'email' command to test")

    def run_command(self, pipeline, opts):
        debug = opts.debug
        log = get_console_logger("Pimlico", debug=debug)

        dry_run = opts.dry_run
        if dry_run:
            log.info("DRY RUN")
            log.info("Running all pre-execution checks, but not executing any modules")
        preliminary = opts.preliminary
        if preliminary:
            log.info("PRELIMINARY RUN")
            log.info("Allowing modules with multiple-dataset inputs to execute even if not all the datasets are ready")
        step = opts.step
        if step:
            log.info("STEP MODE")
            log.info("Running the module(s) in super-verbose, interactive step-mode to debug")
            pipeline.enable_step()

        if opts.modules is None or len(opts.modules) == 0:
            # No module name given: default to next one that's ready to run
            modules = [(module_name, pipeline[module_name]) for module_name in pipeline.modules]
            ready_modules = [module_name for (module_name, module) in modules
                             if module.module_executable and not module.is_locked()
                             and module.status != "COMPLETE" and module.all_inputs_ready()]
            if len(ready_modules) == 0:
                print >>sys.stderr, "No modules not already completed have all their inputs ready: no module name to " \
                                    "default to"
                sys.exit(1)
            else:
                module_specs = [ready_modules[0]]
                log.info("No module name specified. Defaulting to next unexecuted, ready module: '%s'" %
                         module_specs[0])
        else:
            orig_module_specs = opts.modules

            module_specs = []
            for module_spec in orig_module_specs:
                # In the case of a multi-stage module allow a list to be output of available stages
                module_name, __, stage_name = module_spec.rpartition(":")
                if stage_name in ["?", "help"]:
                    # Just output stage names and exit
                    module = pipeline[module_name]
                    if not isinstance(module, MultistageModuleInfo):
                        print "%s is not a multi-stage module" % module_name
                        sys.exit(1)
                    print "Module stages: %s" % ", ".join(stage.name for stage in module.stages)
                    sys.exit(0)
                elif stage_name in ["*", "all"]:
                    # Execute all stages at once, by expanding the list of modules to include all this one's stages
                    module = pipeline[module_name]
                    # Only makes sense with a multistage module
                    if not isinstance(module, MultistageModuleInfo):
                        print "%s is not a multi-stage module: tried to execute all stages (%s)" % (module_name, module_spec)
                        sys.exit(1)
                    module_specs.extend(["%s:%s" % (module_name, stage.name) for stage in module.stages])
                else:
                    # Pass through unchanged
                    # If this has a stage specifier, fine: the pipeline makes the stage module available by that name
                    module_specs.append(module_spec)

        pipeline_name = "'%s'" % pipeline.name if pipeline.variant == "main" else \
            "'%s' (variant '%s')" % (pipeline.name, pipeline.variant)
        log.info("Using pipeline %s" % pipeline_name)
        if pipeline.local_config_sources:
            log.info("Loaded local config from: %s" % ", ".join(pipeline.local_config_sources))

        try:
            check_and_execute_modules(pipeline, module_specs, force_rerun=opts.force_rerun, debug=debug, log=log,
                                      all_deps=opts.all_deps, check_only=dry_run, exit_on_error=opts.exit_on_error,
                                      preliminary=preliminary, email=opts.email)
        except (ModuleInfoLoadError, ModuleNotReadyError), e:
            if debug:
                print_exc()
                if hasattr(e, "cause") and e.cause is not None:
                    print >>sys.stderr, "Caused by: %s" % "".join(format_exception_only(type(e.cause), e.cause)),
            # See whether the problem came from a specific module
            module_name = getattr(e, "module_name", None)
            if module_name is not None:
                error_type = ("Error loading module info for %s" % module_name) if type(e) is ModuleInfoLoadError else \
                    ("Error: module '%s' not ready to run" % module_name)
                print >>sys.stderr, "%s: %s" % (error_type, e)
            else:
                error_type = "Error loading module info" if type(e) is ModuleInfoLoadError else \
                    "Error: module not ready to run"
                print >>sys.stderr, "%s: %s" % (error_type, e)
        except KeyboardInterrupt:
            print >>sys.stderr, "Exiting before execution completed due to user interrupt"
            # Raise the exception so we see the full stack trace
            if debug:
                raise
        else:
            if dry_run:
                log.info("All checks were successful. Modules are ready to run")
