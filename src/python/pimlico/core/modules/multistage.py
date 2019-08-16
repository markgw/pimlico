# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import next
from builtins import zip
from builtins import object
from collections import Counter, OrderedDict
from itertools import takewhile, dropwhile

from past.types import basestring

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
            return next(dropwhile(
                lambda m_s1: m_s1[0].status == "COMPLETE", zip(self.internal_modules, self.stages)))
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
                takewhile(lambda m_s: m_s[0].status == "COMPLETE", zip(self.internal_modules, self.stages))
            )[-1][1]
            return "COMPLETED STAGE %s" % last_completed.name

    def is_locked(self):
        module, stage = self.get_next_stage()
        if module is None:
            return False
        else:
            return module.is_locked()


def multistage_module(multistage_module_type_name, module_stages, use_stage_option_names=False,
                      module_readable_name=None):
    """
    Factory to build a multi-stage module type out of a series of stages, each of which specifies a module type
    for the stage. The stages should be a list of :class:`ModuleStage` objects.

    """
    # First we check that the whole mini-pipeline fits together
    # Note that this check is done at compile-time, so we'll get errors straight away if we define an invalid MS module
    main_inputs = []
    main_outputs = []
    named_stages = {}
    output_stage_names = {}
    # Keep the options in the order of the modules, to make the help more readable
    option_mapping = OrderedDict()
    option_mapping_by_stage = {}
    multistage_module_readable_name = module_readable_name
    required_outputs = {}

    for stage_num, stage in enumerate(module_stages):
        # Make sure we can identify all of the module connections that provide this stage's inputs
        if stage.connections is None:
            # If connections is not given, we default to just connecting this stage's inputs to the default output of
            # the previous stage
            if stage_num == 0:
                # In this case, we create external connections for each input
                stage.connections = [
                    ModuleInputConnection(mod_input[0]) for mod_input in stage.module_info_cls.module_inputs
                ]
            else:
                stage.connections = [
                    InternalModuleConnection(mod_input[0]) for mod_input in stage.module_info_cls.module_inputs
                ]

        for connection in stage.connections:
            if type(connection) in [InternalModuleConnection, InternalModuleMultipleConnection]:
                if stage_num == 0:
                    raise MultistageModulePreparationError("cannot make an internal connection to the first stage")
                if type(connection) is InternalModuleConnection:
                    cnncts = [(connection.previous_module, connection.output_name)]
                else:
                    cnncts = [
                        (
                            None if isinstance(output, basestring) else output[0],
                            output if isinstance(output, basestring) else output[1]
                        ) for output in connection.outputs
                    ]
                for previous_module, output_name in cnncts:
                    # Look for the previous module we're connecting to
                    if previous_module is None:
                        # Default to the previous one in the sequence
                        previous_stage = module_stages[stage_num - 1]
                    elif previous_module not in named_stages:
                        raise MultistageModulePreparationError(
                            "stage %s connects to a previous module that does not precede it in the stage sequence: %s" %
                            (stage.name, previous_module))
                    else:
                        previous_stage = named_stages[previous_module]
                    # Check that the named output of the previous stage exists
                    if output_name is not None and \
                            output_name not in dict(previous_stage.module_info_cls.module_outputs +
                                                    previous_stage.module_info_cls.module_optional_outputs):
                        raise MultistageModulePreparationError(
                            "stage %s connects to an non-existent output of stage %s: %s" %
                            (stage.name, previous_stage.name, output_name))

                    # Make sure that the required output is produced if it's optional
                    if output_name is not None:
                        required_outputs.setdefault(previous_stage.name, []).append(output_name)
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
                if stage_output_name is not None:
                    # Any outputs that are marked as main outputs should be required (if they're optional)
                    required_outputs.setdefault(stage.name, []).append(stage_output_name)

        stage_mapped_options = []
        # Store a separate mapping for each stage, to make processing easier later
        option_mapping_by_stage[stage.name] = {}
        if stage.option_connections is not None:
            for stage_option_name, main_option_name in stage.option_connections.items():
                # Main options can map to multiple stage options
                option_mapping.setdefault(main_option_name, []).append((stage.name, stage_option_name))
                # Note that we've got a mapping for this stage option
                stage_mapped_options.append(stage_option_name)
                # No particular reason to disallow two options in the same stage being mapped to the same main option
                # Therefore, this also needs to be a list
                option_mapping_by_stage[stage.name].setdefault(main_option_name, []).append(stage_option_name)
        # All stage options must be accessible as multistage module options, so we use a default mapping for any
        # not explicitly mapped
        for stage_option_name in list(stage.module_info_cls.module_options.keys()):
            if stage_option_name not in stage_mapped_options:
                if stage.use_stage_option_names or use_stage_option_names:
                    # We've been explicitly instructed to directly use the stage's option names
                    main_option_name = stage_option_name
                else:
                    # Add prefix to option name to distinguish from those of other stages
                    main_option_name = "%s_%s" % (stage.name, stage_option_name)
                option_mapping.setdefault(main_option_name, []).append((stage.name, stage_option_name))
                option_mapping_by_stage[stage.name].setdefault(main_option_name, []).append(stage_option_name)

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
    duplicate_output_names = [n for (n, c) in Counter([name for (name, dtype) in main_outputs]).items() if c > 1]
    if duplicate_output_names:
        raise MultistageModulePreparationError("multistage module has a duplicate output name: %s" %
                                               ", ".join(duplicate_output_names))
    # Duplicate input names are fine -- they connect multiple internal module inputs to the same external input
    # We take the type, though, from the first one
    main_inputs = remove_duplicates(main_inputs, key=lambda input_name_itype: input_name_itype[0])

    main_module_options = OrderedDict(
        # If a main option is connected to multiple stage options, use the first one's definition
        (main_option_name, named_stages[stg_opts[0][0]].module_info_cls.module_options[stg_opts[0][1]])
        for (main_option_name, stg_opts) in option_mapping.items()
    )

    # Define a ModuleInfo for the multi-stage module
    class ModuleInfo(MultistageModuleInfo):
        module_readable_name = multistage_module_readable_name
        module_type_name = multistage_module_type_name
        module_inputs = main_inputs
        module_outputs = main_outputs
        # Module options for the MS module includes all of the internal modules' options, with prefixes
        module_options = main_module_options
        stages = module_stages

        def __init__(self, module_name, pipeline, **kwargs):
            """
            Overridden to also instantiate all of the internal module infos.

            """
            # Instantiate each internal module in turn
            for stage_num, stage in enumerate(self.stages):
                # Get any addition connections for this stage on the basis of the options
                if stage.extra_connections_from_options is not None:
                    _extra_cntns, _extra_output_cntns = stage.extra_connections_from_options(kwargs.get("options", {}))
                    stage.connections.extend(_extra_cntns)
                    stage.output_connections.extend(_extra_output_cntns)

            super(ModuleInfo, self).__init__(module_name, pipeline, **kwargs)

            # Instantiate each internal module in turn
            for stage_num, stage in enumerate(self.stages):
                # Get the sub-module's options by mapping the names of the appropriate main module options
                sub_options = {}
                for opt_name, opt_val in self.options.items():
                    if opt_name in option_mapping_by_stage[stage.name]:
                        # This main option could even map to multiple stage options (slightly niche use case)
                        for stage_option_name in option_mapping_by_stage[stage.name][opt_name]:
                            # Pass the opt val straight through to the stage's module info
                            sub_options[stage_option_name] = opt_val
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
                            [("%s:%s" % (self.module_name, previous_stage_name), connection.output_name)]
                    elif type(connection) is InternalModuleMultipleConnection:
                        connect_to = []
                        for output_def in connection.outputs:
                            if isinstance(output_def, basestring):
                                previous_module, output_name = None, output_def
                            else:
                                previous_module, output_name = output_def

                            # Get the module we're connecting to
                            if previous_module is None:
                                # Default to the previous one in the sequence
                                previous_stage_name = self.stages[stage_num - 1].name
                            else:
                                previous_stage_name = previous_module
                            connect_to.append(("%s:%s" % (self.module_name, previous_stage_name), output_name))
                        # This will be referred to in the pipeline using a prefixed name
                        input_name = connection.input_name or stage.module_info_cls.module_inputs[0][0]
                        sub_inputs[input_name] = connect_to
                    elif type(connection) is ModuleInputConnection:
                        # Connection to multi-stage module input
                        stage_input_name = connection.stage_input_name or stage.module_info_cls.inputs[0][0]
                        main_input_name = connection.main_input_name or stage_input_name
                        sub_inputs[stage_input_name] = self.inputs[main_input_name]

                # Instantiate the module info for the sub-module
                module_info = stage.module_info_cls(
                    "%s:%s" % (self.module_name, stage.name), self.pipeline, inputs=sub_inputs, options=sub_options,
                    # Ensure that we produce all required outputs
                    optional_outputs=required_outputs.get(stage.name, []),
                )
                # Give the stage a pointer to the main module
                module_info.main_module = self

                # Putting this into internal_modules will cause it to be added to the pipeline's running order
                # along with the other stages (in order) instead of the main module
                self.internal_modules.append(module_info)
                self.named_internal_modules[stage.name] = module_info

                # Check for any new outputs from each stage that are defined as main module outputs
                if stage.output_connections is not None:
                    for connection in stage.output_connections:
                        stage_output_name = connection.stage_output_name or \
                                            (stage.module_info_cls.module_outputs + stage.module_info_cls.module_optional_outputs)[0][0]
                        main_output_name = connection.main_output_name or stage_output_name
                        if main_output_name not in dict(self.module_outputs):
                            try:
                                output_type = dict(module_info.available_outputs)[stage_output_name]
                            except KeyError:
                                raise MultistageModulePreparationError(
                                    "stage %s tried to connect a non-existent output '%s' to the multistage module output" %
                                    (stage.name, stage_output_name))
                            self.module_outputs.append((main_output_name, output_type))
                            output_stage_names[main_output_name] = (stage.name, stage_output_name)
                            if stage_output_name is not None:
                                # Any outputs that are marked as main outputs should be required (if they're optional)
                                required_outputs.setdefault(stage.name, []).append(stage_output_name)
                            self.available_outputs.append((main_output_name, output_type))

        def instantiate_output_reader_setup(self, output_name, datatype):
            # Hand over to the appropriate module that the output came from to do the instantiation
            return self.pipeline["{}:{}".format(self.module_name, output_stage_names[output_name][0])]. \
                instantiate_output_reader_setup(output_stage_names[output_name][1], datatype)

    return ModuleInfo


class ModuleStage(object):
    """
    A single stage in a multi-stage module.

    If no explicit input connections are given, the default input to this module is connected to the default
    output from the previous.

    Connections can be given as a list of ``ModuleConnection`` s.

    Output connections specify that one of this module's outputs should be used as an output from the multi-stage
    module. Optional outputs for the multi-stage module are not currently supported (though could in theory be
    added later). This should be a list of ``ModuleOutputConnection`` s. If none are given for any of the stages,
    the module will have a single output, which is the default output from the last stage.

    Option connections allow you to specify the names that are used for the multistage module's options that
    get passed through to this stage's module options. Simply specify a dict for ``option_connections`` where the
    keys are names module options for this stage and the values are the names that should be used for the multistage
    module's options.

    You may map multiple options from different stages to the same option name for the multistage module. This will
    result in the same option value being passed through to both stages. Note that help text, option type, option
    processing, etc will be taken from the first stage's option (in case the two options aren't identical).

    Options not explicitly mapped to a name will use the name ``<stage_name>_<option_name>``.
    If ``use_stage_option_names=True``, this prefix will not be added: the stage's option names will be used
    directly as the option name of the multistage module. Note that there is a danger of clashing option names
    with this behaviour, so only do it if you know the stages have distinct option names (or should share their
    values where the names overlap).

    Further connections may be produced once processed options are available (when the
    main module's module info is instantiated), by specifying a one-argument function
    as ``extra_connections_from_options``. The argument is the processed option dictionary,
    which will contain the full set of options given the to the main module.

    """
    def __init__(self, name, module_info_cls, connections=None, output_connections=None, option_connections=None,
                 use_stage_option_names=False, extra_connections_from_options=None):
        self.use_stage_option_names = use_stage_option_names
        self.option_connections = option_connections
        self.output_connections = output_connections or []
        self.connections = connections or []
        self.name = name
        self.module_info_cls = module_info_cls
        self.extra_connections_from_options = extra_connections_from_options


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


class InternalModuleMultipleConnection(ModuleConnection):
    """
    Connection between the outputs of multiple modules and the input to another
    (which must be a multiple input).

    ``outputs`` should be a list of (``module_name``, ``output_name``) pairs,
    or just strings giving the output name, assumed to be from the previous module.

    """
    def __init__(self, input_name, outputs):
        self.outputs = outputs
        self.input_name = input_name


class ModuleInputConnection(ModuleConnection):
    """
    Connection of a sub-module's input to an input to the multi-stage module.

    If `main_input_name` is not given, the name for the input to the multistage module will be identical to the
    stage input name. This might lead to unintended behaviour if multiple inputs end up with the same name, so you
    can specify a different name if necessary to avoid clashes.

    If multiple inputs (e.g. from different stages) are connected to the same main input name, they will take
    input from the same previous module output. Nothing clever is done to unify the type requirements, however:
    the first stage's type requirement is used for the main module's input.

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
