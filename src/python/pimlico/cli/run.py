import sys
from traceback import print_exc, format_exception_only

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.cli.util import print_execution_error
from pimlico.core.modules.base import ModuleInfoLoadError
from pimlico.core.modules.execute import check_and_execute_modules, ModuleExecutionError
from pimlico.core.modules.multistage import MultistageModuleInfo
from pimlico.utils.logging import get_console_logger


class RunCmd(PimlicoCLISubcommand):
    """
    Main command for executing Pimlico modules from the command line `run` command.

    :param pipeline: PipelineConfig instance
    :param opts: cmd line opts
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

    def run_command(self, pipeline, opts):
        debug = opts.debug
        log = get_console_logger("Pimlico", debug=debug)

        dry_run = opts.dry_run
        if dry_run:
            log.info("DRY RUN")
            log.info("Running all pre-execution checks, but not executing any modules")

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
            module_specs = opts.modules
            for module_spec in module_specs:
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

        pipeline_name = "'%s'" % pipeline.name if pipeline.variant == "main" else \
            "'%s' (variant '%s')" % (pipeline.name, pipeline.variant)
        log.info("Using pipeline %s" % pipeline_name)
        if pipeline.local_config_sources:
            log.info("Loaded local config from: %s" % ", ".join(pipeline.local_config_sources))

        try:
            check_and_execute_modules(pipeline, module_specs, force_rerun=opts.force_rerun, debug=debug, log=log,
                                      all_deps=opts.all_deps, check_only=dry_run)
        except ModuleInfoLoadError, e:
            if debug:
                print_exc()
                if e.cause is not None:
                    print >>sys.stderr, "Caused by: %s" % "".join(format_exception_only(type(e.cause), e.cause)),
            # See whether the problem came from a specific module
            module_name = getattr(e, "module_name", None)
            if module_name is not None:
                print >>sys.stderr, "Error loading module '%s': %s" % (module_name, e)
        except ModuleExecutionError, e:
            if debug:
                print >>sys.stderr, "Top-level error"
                print >>sys.stderr, "---------------"
                print_exc()
                print_execution_error(e)
            # See whether the problem came from a specific module
            module_name = getattr(e, "module_name", None)
            if module_name is not None:
                print >>sys.stderr, "Error executing module '%s': %s" % (module_name, e)
        except KeyboardInterrupt:
            print >>sys.stderr, "Exiting before execution completed due to user interrupt"
            # Raise the exception so we see the full stack trace
            if debug:
                raise
        else:
            if dry_run:
                log.info("All checks were successful. Modules are ready to run")
