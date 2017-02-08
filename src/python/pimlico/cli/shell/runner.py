from pimlico.cli.shell.base import DataShell
from pimlico.cli.shell.commands import BASIC_SHELL_COMMANDS


def shell_cmd(pipeline, opts):
    module_name = opts.module_name
    output_name = opts.output_name
    print "Loading %s of module '%s'" % \
          ("default output" if output_name is None else "output '%s'" % output_name, module_name)
    data = pipeline[module_name].get_output(output_name)
    print "Datatype: %s" % data.datatype_name
    if not data.data_ready():
        print "Warning: the data is not ready yet, so you might have problems querying it"

    print """
Pimlico dataset shell
=====================
The dataset shell provides you with a variety of ways to query the contents
of a Pimlico datatype instance. The commands you can use to query the
dataset depend on its datatype: some datatypes will provide their own set of
commands specific to the sort of data they contain.

For help on using any of the commands, use the 'help' command, with the
command name as an argument.

You can also run arbitrary Python commands, operating on the dataset usin
the name 'data'. The shell will try to execute anything you type that it
doesn't recognise as an available command in this way.
"""
    launch_shell(data)


def launch_shell(data):
    """
    Starts a shell to view and query the given datatype instance.

    """
    commands = BASIC_SHELL_COMMANDS + data.shell_commands
    shell = DataShell(data, commands)
    print "Available commands for this datatype: %s" % ", ".join(
        "%s%s" % (c.commands[0],
                  " (%s)" % ", ".join(c.commands[1:]) if len(c.commands) > 1 else "") for c in commands)
    shell.cmdloop()
