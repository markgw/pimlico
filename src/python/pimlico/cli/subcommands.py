

class PimlicoCLISubcommand(object):
    """
    Base class for defining subcommands to the main command line tool.

    This allows us to split up subcommands, together with all their arguments/options and their functionality,
    since there are quite a lot of them.

    """
    command_name = None
    command_help = None

    def add_arguments(self, parser):
        raise NotImplementedError

    def run_command(self, pipeline, opts):
        raise NotImplementedError
