===============
Pipeline config
===============

A Pimlico pipeline, as read from a config file (:class:`pimlico.core.config.PipelineConfig`) contains all the
information about the pipeline being processed and provides access to specific modules in it. A config file
looks much like a standard `.ini` file, with sections headed by `[section_name]` headings, containing key-value
parameters of the form `key=value`.

Each section, except for `vars` and `pipeline`, defines a module instance in the pipeline. Some of these can
be executed, others act as filters on the outputs of other modules, or input readers.

Each section that defines a module has a `type` parameter. Usually, this is a fully-qualified Python package
name that leads to the module type's Python code (that package containing the `info` Python module). A special
type is `alias`. This simply defines a module alias -- an alternative name for an already defined module. It
should have exactly one other parameter, `input`, specifying the name of the module we're aliasing.

Special sections
----------------

- vars:
    May contain any variable definitions, to be used later on in the pipeline. Further down, expressions like
    `%(varname)s` will be expanded into the value assigned to `varname` in the vars section.
- pipeline:
    Main pipeline-wide configuration. The following options are required for every pipeline:

    * `name`: a single-word name for the pipeline, used to determine where files are stored
    * `release`: the release of Pimlico for which the config file was written. It is considered compatible with
      later minor versions of the same major release, but not with later major releases. Typically, a user
      receiving the pipeline config will get hold of an appropriate version of the Pimlico codebase to run it
      with.

    Other optional settings:

    * `python_path`: a path or paths, relative to the directory containing the config file, in which Python
      modules/packages used by the pipeline can be found. Typically, a config file is distributed with a
      directory of Python code providing extra modules, datatypes, etc. Multiple paths are separated by colons (:).

Special variable substitutions
------------------------------

Certain variable substitutions are always available, in addition to those defined in `vars` sections.

- `pimlico_root`:
    Root directory of Pimlico, usually the directory `pimlico/` within the project directory.
- `project_root`:
    Root directory of the whole project. Current assumed to always be the parent directory of `pimlico_root`.
- `output_dir`:
    Path to output dir (usually `output` in Pimlico root).
- `long_term_store`:
    Long-term store base directory being used under the current config. Can be used to link to data from
    other pipelines run on the same system. This is the value specified in the :ref:`local config file <local-config>`.
- `short_term_store`:
    Short-term store base directory being used under the current config. Can be used to link to data from
    other pipelines run on the same system. This is the value specified in the :ref:`local config file <local-config>`.

Directives
----------

Certain special directives are processed when reading config files. They are lines that begin with `%%`, followed
by the directive name and any arguments.

- `variant`:
    Allows a line to be included only when loading a particular variant of a pipeline. The variant name is
    specified as part of the directive in the form: `variant:variant_name`. You may include the line in more
    than one variant by specifying multiple names, separated by commas (and no spaces). You can use the default
    variant "main", so that the line will be left out of other variants. The rest of the line, after the directive
    and variant name(s) is the content that will be included in those variants.

    .. code-block:: ini
       :emphasize-lines: 3,4

       [my_module]
       type=path.to.module
       %%variant:main size=52
       %%variant:smaller size=7

- `novariant`:
    A line to be included only when not loading a variant of the pipeline. Equivalent to `variant:main`.

    .. code-block:: ini
       :emphasize-lines: 3

       [my_module]
       type=path.to.module
       %%novariant size=52
       %%variant:smaller size=7

- `include`:
    Include the entire contents of another file. The filename, specified relative to the config file in which the
    directive is found, is given after a space.
- `abstract`:
    Marks a config file as being abstract. This means that Pimlico will not allow it to be loaded as a top-level
    config file, but only allow it to be included in another config file.
- `copy`:
    Copies all config settings from another module, whose name is given as the sole argument. May be used multiple
    times in the same module and later copies will override earlier. Settings given explicitly in the module's
    config override any copied settings. The following settings are not copied: input(s), `filter`, `outputs`,
    `type`.

Multiple parameter values
-------------------------

Sometimes you want to write a whole load of modules that are almost identical, varying in just one or two
parameters. You can give a parameter multiple values by writing them separated by vertical bars (`|`). The module
definition will be expanded to produce a separate module for each value, with all the other parameters being
identical.

For example, this will produce three module instances, all having the same `num_lines` parameter, but each with
a different `num_chars`:

.. code-block:: ini
   :emphasize-lines: 4

   [my_module]
   type=module.type.path
   num_lines=10
   num_chars=3|10|20

You can even do this with multiple parameters of the same module and the expanded modules will cover all
combinations of the parameter assignments.

For example:

.. code-block:: ini
   :emphasize-lines: 3,4

   [my_module]
   type=module.type.path
   num_lines=10|50|100
   num_chars=3|10|20

Each module will be given a distinct name, based on the varied parameters. If just one is varied, the names
will be of the form `module_name[param_value]`. If multiple parameters are varied at once, the names will be
`module_name[param_name0=param_value0~param_name1=param_value1~...]`. So, the first example above will produce:
`my_module[3]`, `my_module[10]` and `my_module[20]`. And the second will produce: `my_module[num_lines=10~num_chars=3]`,
`my_module[num_lines=10~num_chars=10]`, etc.

You can also specify your own identifier for the alternative parameter values, instead of using the values
themselves (say, for example, if it's a long file path). Specify it surrounded by curly braces at the
start of the value in the alternatives list. For example:

.. code-block:: ini
   :emphasize-lines: 3

   [my_module]
   type=module.type.path
   file_path={small}/home/me/data/corpus/small_version|{big}/home/me/data/corpus/big_version

This will result in the modules `my_module[small]` and `my_module[big]`, instead of using the whole file
path to distinguish them.

You can change the behaviour of alternative values using the `tie_alts` option. `tie_alts=T` will cause
parameters within the same module that have multiple alternatives to be expanded in parallel, rather than
taking the product of the alternative sets. So, if option_a has 5 values and option_b has 5 values, instead
of producing 25 pipeline modules, we'll only produce 5, matching up each pair of values in their alternatives.

.. code-block:: ini

   [my_module]
   type=module.type.path
   tie_alts=T
   option_a=1|2|3
   option_b=one|two|three

If a module takes input from a module that has been expanded into multiple versions for alternative parameter
values, it too will automatically get expanded, as if all the multiple versions of the previous module had
been given as alternative values for the input parameter. For example, the following will result in 3 versions
of `my_module` (`my_module[1]`, etc) and 3 corresponding versions of `my_next_module` (`my_next_module[1]`, etc):

.. code-block:: ini

   [my_module]
   type=module.type.path
   option_a=1|2|3

   [my_next_module]
   type=another.module.type.path
   input=my_module

Where possible, names given to the alternative parameter values in the first module will be carried through
to the next.
