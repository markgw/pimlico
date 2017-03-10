from pimlico.cli.subcommands import PimlicoCLISubcommand


class PythonShellCmd(PimlicoCLISubcommand):
    command_name = "python"
    command_help = "Load the pipeline config and enter a Python interpreter with access to it in the environment"

    def add_arguments(self, parser):
        parser.add_argument("script", nargs="?", help="Script file to execute. Omit to enter interpreter")

    def run_command(self, pipeline, opts):
        from code import interact
        print "Loaded pipeline config"
        print "PipelineConfig object is available as variable 'pipeline' (or 'p')"
        local = {"pipeline": pipeline, "p": pipeline}

        if opts.script:
            # Script given on the command line, execute it
            execfile(opts.script, local)
        else:
            # Enter the interpreter
            interact(local=local)
