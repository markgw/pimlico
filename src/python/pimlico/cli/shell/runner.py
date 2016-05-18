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
    launch_shell(data)


def launch_shell(data):
    """
    Starts a shell to view and query the given datatype instance.

    """
    commands = BASIC_SHELL_COMMANDS + data.shell_commands
    shell = DataShell(data, commands)
    print "Available commands for this datatype: %s" % ", ".join(
        "%s%s" % (c.commands[0],
                  " (%s)" % ", ".join(c.commands[1:])) if len(c.commands) > 1 else "" for c in commands)
    print "Loaded output data is available as 'data'"
    shell.cmdloop()
