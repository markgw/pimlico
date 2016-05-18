

def multistage_module(stages, outputs=None):
    """
    Factory to build a multi-stage module type out of a series of stages, each of which specifies a module type
    for the stage.

    The outputs to the multi-stage module are given by outputs, which should be a list of (stage name, output name)
    pairs, where the stage name represents one of the stages and the output name is one of its outputs. If the outputs
    are not pairs, but just strings, they are taken to refer to the last stage. If no outputs are given, the
    default output of the last stage is the multi-stage module's output.

    """
    # TODO


class ModuleStage(object):
    """
    A single stage in a multi-stage module.

    If no previous module name is given, the previous one in the sequence of stages is assumed.

    If no explicit input connections are given, the default input to this module is connected to the default
    output from the previous.

    Connections can be given as a list of (output, input) pairs, where output is the name of an output from
    the named previous module and input is the name of an input to the current module.

    If this is the first stage in the multi-stage module, the output names in connections are used as input
    names for the multi-stage module, which are connected to the inputs of this module.

    """
    def __init__(self, name, module_info, connections=None, previous_module=None):
        self.previous_module = previous_module
        self.connections = connections
        self.name = name
        self.module_info = module_info
