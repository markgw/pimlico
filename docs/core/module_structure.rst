========================
Pimlico module structure
========================

This document describes the code structure for Pimlico module types in full.

For a basic guide to writing your own modules, see :doc:`/guides/module`.

.. todo::

   Finish the missing parts of this doc below


For many generic or common tasks, you can use one of Pimlico's
:mod:`built-in module types <pimlico.modules>`, but often you will
want to write your own module code to do some of the processing in
your pipeline.

The :doc:`module-writing guide </guides/module>` takes you through
how to write your own module type and use it in your pipeline. This
document is a more comprehesive documentation of the structure of
module definitions and execution code.

Code layout
===========
A module is defined by a Python package containing at least two Python
files (i.e. Python modules):

 * ``info.py``. This contains a class called ``ModuleInfo`` that provides
   all the structural information about a module: its inputs, outputs,
   options, etc. This is instantiated for each module of this type
   in a pipeline when the pipeline is loaded.
 * ``execute.py``. This contains a class called ``ModuleExecutor`` that
   has a method that is called when the module is run. The ``execute``
   Python module is only imported when a module is about to be run,
   so is free to contain package imports that depend on having special
   software packages installed.

You should take care when writing ``info.py`` not to import any non-standard
Python libraries or have any time-consuming operations
that get run when it gets imported, as it's loaded whenever a pipeline
containing that module type is loaded up, when checking module status for example,
before software dependencies are resolved.

``execute.py``, on the other hand, will only get imported when the module is to be
run, after dependency checks.

Pimlico provides a wizard in the :ref:`command_newmodule` command that
guides you through the most common tasks in creating a new module.
At the end, it will generate a template to get you started with your module's code.
You then just need to fill
in the gaps and write the code for what the module actually does.
It does not, however, cover every type of module definition that you
might want – just the most common cases.

Metadata: info.py
=================
The ModuleInfo
--------------
Module metadata (everything apart from what happens when it's actually run)
is defined in ``info.py`` as a class called ``ModuleInfo``.
Let's take the built-in module :mod:`~pimlico.modules.corpora.corpus_stats` –
which counts up tokens, sentences, etc in a corpus – as an example.
(It's slightly modified here for the example.)

.. code-block:: py

   from pimlico.core.modules.base import BaseModuleInfo
   from pimlico.datatypes import GroupedCorpus, NamedFile
   from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


   class ModuleInfo(BaseModuleInfo):
       module_type_name = "corpus_stats"
       module_readable_name = "Corpus statistics"
       module_inputs = [("corpus", GroupedCorpus(TokenizedDocumentType()))]
       module_outputs = [("stats", NamedFile("stats.json"))]
       module_options = {
           "min_sent_len": {
               "type": int,
               "help": "Filter out any sentences shorter than this length",
           }
       }


The ``ModuleInfo`` should always be a subclass of
:class:`~pimlico.core.modules.base.BaseModuleInfo`. There are
some subclasses that you might want to use instead
(e.g., see :doc:`/guides/map_module`), but here we just use the basic one.

Certain class-level attributes should pretty much always be overridden:

- ``module_type_name``: A name used to identify the module internally
- ``module_readable_name``: A human-readable short description of the module
- ``module_inputs``: Most modules need to take input from another module (though not all)
- ``module_outputs``: Describes the outputs that the module will produce, which may then be used as inputs to another module

Inputs
------
**Inputs** are given as pairs ``(name, type)``, where ``name`` is a short name to
identify the input and ``type`` is the datatype
that the input is expected to have. Here, and most commonly, this is an instance of a subclass of
:class:`~pimlico.datatypes.base.PimlicoDatatype`. Pimlico will check that any
dataset supplied for this input is of a compatible datatype.

Here we take just a single input. It is a corpus of the standard type that Pimlico
uses for sequential document corpora :class:`~pimlico.datatypes.corpora.GroupedCorpus`.
More specifically, it is a corpus with a document type of
:class:`~pimlico.datatypes.corpora.tokenized.TokenizedDocumentType`, or some sub-type.

Outputs
-------
**Outputs** are given in a similar way. It is up to the module's executor
(see below) to ensure that these outputs
get written, but the ModuleInfo describes the datatypes that will be produced,
so that we can use them as input to other modules.

In the example, we produce a single file containing the output of the analysis.

Once a module has been instantiated, its output names and types are available
in its ``available_outputs`` attribute, which can be consulted by its executor and which
is used for typechecking connections to later modules and loading the output
datasets produced by the module.

Output groups
~~~~~~~~~~~~~

.. todo::

   This documentation is being written in advance of the addition of this
   feature. It explains how output groups will be used, but the feature
   is not fully implemented yet!

A module's outputs have no structure: each module just has a list of outputs
identified by their names. The don't typically even have any particular order.

However, sometimes it can be useful to group together some of the outputs,
so that they can easily be used later collectively. Say, for example, a
module produces three corpora, each as a separate output, and also a
``NamedFile`` output containing some analysis. It is useful to be able to
refer to the corpora as a group, rather than having to list them each by
name, if for instance you are using all three to feed into a multiple-input
to a later module. This becomes particularly important if the number of
output corpora is not even statically defined: see below for how the
number of outputs might depend on inputs and options.

A module can define named groups of outputs. Every module, by default, has a
single module group, called ``"all"``.

Once a module info has been instantiated, it has an attribute ``output_groups``
listing the groups. Each group is specified as ``(group_name, [output_name1, ...])``.

.. todo::

   The actual use of these groups hasn't been implemented yet. This
   is how it will work...

In a config file, an output group name can be used in the same way as a
single output name to specify where inputs to a module will come from:
``module_name.output_group_name``. If a group name is given, instead
of a single output name, it will be expanded into a comma-separated
**list of output names** corresponding to that group. Of course, this
will only work if the input in question is a **multiple-input**, allowing
it to accept a comma-separated list of datasets as input.

Alternatively, you may use an output group to provide **alternative**
datasets for an input, just as you usually would using ``|``s. If
you use ``altgroup(module_name.output_group_name)`` as an input to a module,
it will be expanded to ``module_name.output_name1|module_name.output_name2|:...``
to provide each output in the group as an alternative input.
(See :doc:`/core/config` for more on alternative inputs and parameters.)

Optional outputs
~~~~~~~~~~~~~~~~

.. todo::

   Document optional outputs.

   Should include choose_optional_outputs_from_options(options, inputs) for deciding what
   optional outputs to include.

Outputs dependent on options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A module info can supply output names/types that are dependent on the module instance's
inputs and options. This is done by overriding the method ``provide_further_outputs()``.
It is called once the ModuleInfo instance's ``inputs`` and ``options`` attributes
have already been set and preprocessed.

It returns a list just like the statically defined ``module_outputs`` attribute:
pairs of ``(output_name, datatype_instance)``. Once the module info has been
instantiated for a particular module in a pipeline, these outputs will be available
in the ``available_outputs`` attribute, just like any that were defined statically.

Options
-------
Most modules define some **options** that provided control over exactly
what the module does when executed. The values for these can be specified
in the pipeline config file. When the
``ModuleInfo`` is instantiated, the processed options will be available
in its ``options`` attribute.

In the example, there is one option that can be specified in the config file,
like this:

.. code:: ini

   [mymod]
   type=pimlico.modules.corpora.corpus_stats
   input=some_previous_mod
   min_sent_len=5

The option definition provides some help text explaining what the option does,
which is included in the module's documentation, which can be automatically
produced using Sphinx (see :doc:`/guides/docs`).

Its value can be accessed from within the executor's ``execute()`` method using:
``self.info.options["min_sent_len"]``. By this point, the value from the config
file has been checked and preprocessed, so it is an int.

.. todo::

   Fully document module options, including: required, type checking/processing
   and other fancy features.

Software dependencies
---------------------
Many modules rely on external Python packages or other software for their execution.
The ModuleInfo specifies exactly what software is required in such a way that
Pimlico can:

 - check whether the software is available and runable;
 - if possible, install the software if it's not available (e.g. Python packages
   installable via Pip);
 - otherwise, provide instructions on how to install it;
 - in some special cases, run initalization or other preparatory routines
   before the external software is loaded/run.

.. todo::

   Further document specification of software dependencies

More extensive documentation of the Pimlico dependency system is provided
in :doc:`/core/dependencies`.

Execution: execute.py
=====================

.. todo::

   This section is copied from :doc:`/core/module_structure`.
   It needs to be re-written to provide more technical and comprehensive documentation
   of module execution.

Here is a sample executor for the module info given above, placed in the file ``execute.py``.

.. code-block:: py

    from pimlico.core.modules.base import BaseModuleExecutor
    from pimlico.datatypes.arrays import NumpyArrayWriter
    from sklearn.decomposition import NMF

    class ModuleExecutor(BaseModuleExecutor):
        def execute(self):
            input_matrix = self.info.get_input("matrix").array
            self.log.info("Loaded input matrix: %s" % str(input_matrix.shape))

            # Convert input matrix to CSR
            input_matrix = input_matrix.tocsr()
            # Initialize the transformation
            components = self.info.options["components"]
            self.log.info("Initializing NMF with %d components" % components)
            nmf = NMF(components)

            # Apply transformation to the matrix
            self.log.info("Fitting NMF transformation on input matrix" % transform_type)
            transformed_matrix = transformer.fit_transform(input_matrix)

            self.log.info("Fitting complete: storing H and W matrices")
            # Use built-in Numpy array writers to output results in an appropriate format
            with NumpyArrayWriter(self.info.get_absolute_output_dir("w")) as w_writer:
                w_writer.set_array(transformed_matrix)
            with NumpyArrayWriter(self.info.get_absolute_output_dir("h")) as h_writer:
                h_writer.set_array(transformer.components_)

The executor is always defined as a class in ``execute.py`` called ``ModuleExecutor``. It should always be a subclass
of ``BaseModuleExecutor`` (though, again, note that there are more specific subclasses and class factories that we
might want to use in other circumstances).

The ``execute()`` method defines what happens when the module is executed.

The instance of the module's ``ModuleInfo``, complete with **options** from the pipeline config, is available as
``self.info``. A standard Python **logger** is also available, as ``self.log``, and should be used to keep the user updated
on what's going on.

Getting hold of the **input data** is done through the module info's ``get_input()`` method. In the case of a Scipy matrix,
here, it just provides us with the matrix as an attribute.

Then we do whatever our module is designed to do. At the end, we write the output data to the appropriate output
directory. This should always be obtained using the ``get_absolute_output_dir()`` method of the module info, since
Pimlico takes care of the exact location for you.

Most Pimlico datatypes provide a corresponding **writer**, ensuring that the output is written in the correct format
for it to be read by the datatype's reader. When we leave the ``with`` block, in which we give the writer the
data it needs, this output is written to disk.

Pipeline config
===============

Pipeline config files are fully documented in :doc:`/core/config`. Refer to that
for all the details of how modules can be used in pipelines.

.. todo::

   This section is copied from :doc:`/core/module_structure`.
   It needs to be re-written to provide more technical and comprehensive documentation
   of pipeline config.
   NB: config files are fully documented in :doc:`/core/config`, so this just covers how
   ModuleInfo relates to the config.

Our module is now ready to use and we can refer to it in a pipeline config file. We'll assume we've prepared a suitable
Scipy sparse matrix earlier in the pipeline, available as the default output of a module called ``matrix``. Then we
can add section like this to use our new module:

.. code-block:: ini

    [matrix]
    ...(Produces sparse matrix output)...

    [factorize]
    type=myproject.modules.nmf
    components=300
    input=matrix

Note that, since there's only one input, we don't need to give its name. If we had defined multiple inputs, we'd
need to specify this one as ``input_matrix=matrix``.

You can now run the module as part of your pipeline in the usual ways.
