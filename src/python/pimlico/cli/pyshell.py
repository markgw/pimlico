from pimlico.cli.subcommands import PimlicoCLISubcommand


class PimlicoPythonShellContext(object):
    """
    A class used as a static global data structure to provide access to the loaded pipeline when running the
    Pimlico Python shell command.

    This should never be used in any other context to pass around loaded pipelines
    or other global data. We don't do that sort of thing.

    """
    def __init__(self):
        self.pipeline = None


# Make the pipeline available in (effectively) a global variable when we run the shell
# The attribute's non-None value indicates that we're running through the shell and have a pipeline loaded
# In other contexts, this will be None, indicating that we're not running the shell and the pipeline shouldn't be
# accessed in this way
_shell_context = PimlicoPythonShellContext()


class PythonShellCmd(PimlicoCLISubcommand):
    command_name = "python"
    command_help = "Load the pipeline config and enter a Python interpreter with access to it in the environment"

    def add_arguments(self, parser):
        parser.add_argument("script", nargs="?", help="Script file to execute. Omit to enter interpreter")
        parser.add_argument("-i", action="store_true", help="Enter interactive shell after running script")

    def run_command(self, pipeline, opts):
        _shell_context.pipeline = pipeline

        if opts.script:
            # Script given on the command line, execute it
            execfile(opts.script)

        if not opts.script or opts.i:
            # Enter the interpreter
            from code import interact

            print "Loaded pipeline config"
            print "PipelineConfig object is available as variable 'pipeline' (or 'p')"
            local = {"pipeline": pipeline, "p": pipeline}

            interact(local=local)


def get_pipeline():
    """
    This function may be used in scripts that are expected to be run exclusively from the Pimlico Python shell
    command (``python``) to get hold of the pipeline that was specified on the command line and
    loaded when the shell was started.

    """
    if _shell_context.pipeline is None:
        raise ShellContextError("tried to access the pipeline loaded by the Pimlico Python shell, but not is "
                                "available. This probably means that this has been called from a context other "
                                "than the Pimlico Python shell and should not be used")
    return _shell_context.pipeline


class ShellContextError(Exception):
    pass
