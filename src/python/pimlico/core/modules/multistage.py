from collections import Counter, OrderedDict
from itertools import takewhile, dropwhile

from pimlico.cli.status import status_colored
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.utils.core import remove_duplicates


class MultistageModuleInfo(BaseModuleInfo):
    """
    Base class for multi-stage modules. You almost certainly don't want to override this yourself, but use the
    factory method instead. It exists mainly for providing a way of identifying multi-stage modules.

    """
    module_executable = True
    stages = None  # Set by factory

    def __init__(self, module_name, pipeline, **kwargs):
        super(MultistageModuleInfo, self).__init__(module_name, pipeline, **kwargs)
        self.internal_modules = []
        self.named_internal_modules = {}

    def typecheck_inputs(self):
        """
        Overridden to check internal output-input connections as well as the main module's inputs.

        """
        super(MultistageModuleInfo, self).typecheck_inputs()
        for submodule in self.internal_modules:
            submodule.typecheck_inputs()

    def get_software_dependencies(self):
        # Include dependencies for each submodule
        deps = super(MultistageModuleInfo, self).get_software_dependencies()
        for module in self.internal_modules:
            deps.extend(module.get_software_dependencies())
        return deps

    def get_input_software_dependencies(self):
        # Only check the sub-modules' deps
        # No need to call super, since it will only duplicate some of the submodules' inputs
        return [dep for module in self.internal_modules for dep in module.get_input_software_dependencies()]

    def check_ready_to_run(self):
        problems = super(MultistageModuleInfo, self).check_ready_to_run()
        for module in self.internal_modules:
            problems.extend(module.check_ready_to_run())
        return problems

    def get_detailed_status(self):
        return super(MultistageModuleInfo, self).get_detailed_status() + [
            "Stages in multi-stage module: %s" % ", ".join(
                status_colored(mod, stage.name) for (stage, mod) in zip(self.stages, self.internal_modules)
            )
        ]

    def reset_execution(self):
        # Reset the main module
        super(MultistageModuleInfo, self).reset_execution()
        # Also reset all stage modules
        for module in self.internal_modules:
            module.reset_execution()

    @classmethod
    def get_key_info_table(cls):
        """
        Add the stages into the key info table.

        """
        return super(MultistageModuleInfo, cls).get_key_info_table() + [
            ["Stages", ", ".join(stage.name for stage in cls.stages)],
        ]

    def get_next_stage(self):
        """
        If there are more stages to be executed, returns a pair of the module info and stage definition.
        Otherwise, returns (None, None)

        """
        try:
            return dropwhile(
                lambda (m, s): m.status == "COMPLETE", zip(self.internal_modules, self.stages)).next()
        except StopIteration:
            # No more left to execute
            return (None, None)

    @property
    def status(self):
        # Override status to compute it from sub-module statuses
        stage_statuses = [m.status for m in self.internal_modules]
        if all(s == "COMPLETE" for s in stage_statuses):
            return "COMPLETE"
        elif not any(s == "COMPLETE" for s in stage_statuses):
            return "UNEXECUTED"
        else:
            last_completed = list(
                takewhile(lambda (m, s): m.status == "COMPLETE", zip(self.internal_modules, self.stages))
            )[-1][1]
            return "COMPLETED STAGE %s" % last_completed.name

    def is_locked(self):
        module, stage = self.get_next_stage()
        if module is None:
            return False
        else:
            return module.is_locked()


def multistage_module(multistage_module_type_name, module_stages):
    """
    Factory to build a multi-stage module type out of a series of stages, each of which specifies a module type
    for the stage.

    The outputs to the multi-stage module are given by outputs, which should be a list of (stage name, output name)
    pairs, where the stage name represents one of the stages and the output name is one of its outputs. If the outputs
    are not pairs, but just strings, they are taken to refer to the last stage. If no outputs are given, the
    default output of the last stage is the multi-stage module's output.

    """
    # First we check that the whole mini-pipeline fits together
    # Note that this check is done at compile-time, so we'll get errors straight away if we define an invalid MS module
    main_inputs = []
    main_outputs = []
    named_stages = {}
    output_stage_names = {}
    # Like pipeline.used_outputs (and added to it when necessary)
    used_internal_outputs = {}

    for stage_num, stage in enumerate(module_stages):
        # Make sure we can identify all of the module connections that provide this stage's inputs
        for connection in stage.connections:
            if type(connection) is InternalModuleConnection:
                if stage_num == 0:
                    raise MultistageModulePreparationError("cannot make an internal connection to the first stage")
                # Look for the previous module we're connecting to
                if connection.previous_module is None:
                    # Default to the previous one in the sequence
                    previous_stage = module_stages[stage_num - 1]
                elif connection.previous_module not in named_stages:
                    raise MultistageModulePreparationError(
                        "stage %s connects to a previous module that does not precede it in the stage sequence: %s" %
                        (stage.name, connection.previous_module))
                else:
                    previous_stage = named_stages[connection.previous_module]
                # Check that the named output of the previous stage exists
                if connection.output_name is not None and \
                        connection.output_name not in dict(previous_stage.module_info_cls.module_outputs +
                                                           previous_stage.module_info_cls.module_optional_outputs):
                    raise MultistageModulePreparationError(
                        "stage %s connects to an non-existent output of stage %s: %s" %
                        (stage.name, previous_stage.name, connection.output_name))

                # Add to the internal module's list of used outputs
                used_internal_outputs.setdefault(previous_stage, set([])).add(connection.output_name)
            elif type(connection) is ModuleInputConnection:
                # Connection to multi-stage module input
                # Get the input type for the stage input
                stage_input_name = connection.stage_input_name or stage.module_info_cls.inputs[0][0]
                try:
                    input_type = dict(stage.module_info_cls.module_inputs)[stage_input_name]
                except KeyError:
                    raise MultistageModulePreparationError(
                        "stage %s tried to connect a non-existent input '%s' to the multistage module input" %
                        (stage.name, stage_input_name))
                main_input_name = connection.main_input_name or stage_input_name
                main_inputs.append((main_input_name, input_type))

        # Process any outputs from this stage that are defined as main module outputs
        if stage.output_connections is not None:
            for connection in stage.output_connections:
                stage_output_name = connection.stage_output_name or \
                                    (stage.module_info_cls.module_outputs + stage.module_info_cls.module_optional_outputs)[0][0]
                try:
                    output_type = dict(stage.module_info_cls.module_outputs + stage.module_info_cls.module_optional_outputs)[
                        stage_output_name]
                except KeyError:
                    raise MultistageModulePreparationError(
                        "stage %s tried to connect a non-existent output '%s' to the multistage module output" %
                        (stage.name, stage_output_name))
                main_output_name = connection.main_output_name or stage_output_name
                main_outputs.append((main_output_name, output_type))
                output_stage_names[main_output_name] = (stage.name, stage_output_name)

        named_stages[stage.name] = stage

    # If no inputs were specified, use the default
    if len(main_inputs) == 0:
        main_inputs.append(module_stages[0].module_info_cls.module_inputs[0])
    # Same with the outputs
    if len(main_outputs) == 0:
        main_outputs.append(
            (module_stages[-1].module_info_cls.module_outputs + module_stages[-1].module_info_cls.module_optional_outputs)[0])
        output_stage_names[main_outputs[-1][0]] = (module_stages[-1].name, main_outputs[-1][0])
    # Check we've not ended up with duplicate output names
    duplicate_output_names = [n for (n, c) in Counter([name for (name, dtype) in main_outputs]).iteritems() if c > 1]
    if duplicate_output_names:
        raise MultistageModulePreparationError("multistage module has a duplicate output name: %s" %
                                               ", ".join(duplicate_output_names))
    # Duplicate input names are fine -- they connect multiple internal module inputs to the same external input
    # We take the type, though, from the first one
    main_inputs = remove_duplicates(main_inputs, key=lambda (input_name, itype): input_name)

    # Define a ModuleInfo for the multi-stage module
    class ModuleInfo(MultistageModuleInfo):
        module_readable_name = multistage_module_type_name
        module_type_name = multistage_module_type_name
        module_inputs = main_inputs
        module_outputs = main_outputs
        # Module options for the MS module includes all of the internal modules' options, with prefixes
        # Keep the options in the order of the modules, to make the help more readable
        module_options = OrderedDict(("%s_%s" % (stage.name, opt_name), opt_def) for stage in module_stages
                                     for (opt_name, opt_def) in stage.module_info_cls.module_options.iteritems())
        stages = module_stages

        def __init__(self, module_name, pipeline, **kwargs):
            """
            Overridden to also instantiate all of the internal module infos.

            """
            super(ModuleInfo, self).__init__(module_name, pipeline, **kwargs)
            # Before instantiating internal modules, make available the list of used outputs from within the MS module
            pipeline.used_outputs.update(dict(
                ("%s:%s" % (self.module_name, stage_name), cntns)
                for (stage_name, cntns) in used_internal_outputs.iteritems()
            ))

            # Instantiate each internal module in turn
            for stage_num, stage in enumerate(self.stages):
                # Get the sub-module's options by removing prefixes
                sub_options = dict((opt_name.partition("%s_" % stage.name)[2], opt_val)
                                   for (opt_name, opt_val) in self.options.iteritems())
                # Get a list of inputs suitable to instantiate the module info
                sub_inputs = {}
                for connection in stage.connections:
                    if type(connection) is InternalModuleConnection:
                        # Get the module we're connecting to
                        if connection.previous_module is None:
                            # Default to the previous one in the sequence
                            previous_stage_name = self.stages[stage_num-1].name
                        else:
                            previous_stage_name = connection.previous_module
                        # This will be referred to in the pipeline using a prefixed name
                        input_name = connection.input_name or stage.module_info_cls.module_inputs[0][0]
                        # We don't currently allow additional output specifiers within multistage modules, but
                        # there's no reason why we couldn't
                        sub_inputs[input_name] = \
                            [("%s:%s" % (self.module_name, previous_stage_name), connection.output_name, [])]
                    elif type(connection) is ModuleInputConnection:
                        # Connection to multi-stage module input
                        stage_input_name = connection.stage_input_name or stage.module_info_cls.inputs[0][0]
                        main_input_name = connection.main_input_name or stage_input_name
                        sub_inputs[stage_input_name] = self.inputs[main_input_name]
                # Instantiate the module info for the sub-module
                module_info = stage.module_info_cls(
                    "%s:%s" % (self.module_name, stage.name), self.pipeline, inputs=sub_inputs, options=sub_options
                )
                # Give the stage a pointer to the main module
                module_info.main_module = self

                self.internal_modules.append(module_info)
                self.named_internal_modules[stage.name] = module_info
                # Also add the module into the pipeline, with the MS module prefix, so we can make connections
                # NB I haven't tried this since I changed the way pipelines are loaded, so it could have problems
                self.pipeline.append_module(module_info)

        def instantiate_output_datatype(self, output_name, output_datatype):
            # Hand over to the appropriate module that the output came from to do the instantiation
            return self.pipeline["%s:%s" % (self.module_name, output_stage_names[output_name][0])].\
                instantiate_output_datatype(output_stage_names[output_name][1], output_datatype)

    return ModuleInfo


class ModuleStage(object):
    """
    A single stage in a multi-stage module.

    If no explicit input connections are given, the default input to this module is connected to the default
    output from the previous.

    Connections can be given as a list of `ModuleConnection`s.

    Output connections specify that one of this module's outputs should be used as an output from the multi-stage
    module. Optional outputs for the multi-stage module are not currently supported (though could in theory be
    added later). This should be a list of `ModuleOutputConnection`s. If none are given for any of the stages,
    the module will have a single output, which is the default output from the last stage.

    """
    def __init__(self, name, module_info_cls, connections=None, output_connections=None):
        self.output_connections = output_connections
        self.connections = connections
        self.name = name
        self.module_info_cls = module_info_cls


class ModuleConnection(object):
    pass


class InternalModuleConnection(ModuleConnection):
    """
    Connection between the output of one module in the multi-stage module and the input to another.

    May specify the name of the previous module that a connection should be made to. If this is not given,
    the previous module in the sequence will be assumed.

    If `output_name=None`, connects to the default output of the previous module.

    """
    def __init__(self, input_name, output_name=None, previous_module=None):
        self.output_name = output_name
        self.input_name = input_name
        self.previous_module = previous_module


class ModuleInputConnection(ModuleConnection):
    """
    Connection of a sub-module's input to an input to the multi-stage module.

    If `main_input_name` is not given, the name for the input to the multistage module will be identical to the
    stage input name. This will lead to an error if multiple inputs end up with the same name, so you can specify
    a different name if necessary to avoid clashes.

    If `stage_input_name` is not given, the module's default input will be connected.

    """
    def __init__(self, stage_input_name=None, main_input_name=None):
        self.stage_input_name = stage_input_name
        self.main_input_name = main_input_name


class ModuleOutputConnection(object):
    """
    Specifies the connection of a sub-module's output to the multi-stage module's output.
    Works in a similar way to `ModuleInputConnection`.

    """
    def __init__(self, stage_output_name=None, main_output_name=None):
        self.stage_output_name = stage_output_name
        self.main_output_name = main_output_name


class MultistageModulePreparationError(Exception):
    pass
