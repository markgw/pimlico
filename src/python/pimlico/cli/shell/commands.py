"""
Basic set of shell commands that are always available.

"""
from pimlico.cli.shell.base import ShellCommand


class MetadataCmd(ShellCommand):
    commands = ["metadata"]
    help_text = "Display the loaded dataset's metadata"

    def execute(self, shell, *args, **kwargs):
        metadata = shell.data.metadata
        print "\n".join("%s: %s" % (key, val) for (key, val) in metadata.iteritems())


BASIC_SHELL_COMMANDS = [MetadataCmd()]
