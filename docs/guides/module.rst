===========================
  Writing Pimlico modules
===========================

Pimlico comes with a fairly large number of :mod:`module types <pimlico.modules>`
that you can use to run many standard NLP, data processing
and ML tools over your datasets.

For some projects, this is all you need to do. However, often you'll want to mix standard tools with
your own code, for example, using the output from the tools. And, of course, there are many more tools you might
want to run that aren't built into Pimlico: you can still benefit from Pimlico's framework for
data handling, config files and so on.

For a detailed description of the structure of a Pimlico module, see :doc:`/core/module_structure`. This guide takes
you through building a simple module.

.. note::

   In any case where a module will process a corpus one document at a time, you should write a
   :doc:`document map module <map_module>`, which takes care of a lot of things for you, so you only need
   to say what to do with each document.

Code layout
===========
If you've followed the :doc:`basic project setup guide <setup>`, you'll have a project with a directory structure
like this::

   myproject/
       pipeline.conf
       pimlico/
           bin/
           lib/
           src/
           ...
       src/
           python/

If you've not already created the ``src/python`` directory, do that now.

This is where your custom Python code
will live. You can put all of your custom module types and datatypes in there and use them in the same way
as you use the Pimlico core modules and datatypes.

Add this option to the ``[pipeline]`` section of your config file, so Pimlico knows where to find your code:

.. code-block:: ini

    python_path=src/python

To follow the conventions used in Pimlico's codebase, we'll create the following package structure in ``src/python``::

    src/python/myproject/
        __init__.py
        modules/
            __init__.py
        datatypes/
            __init__.py

Write a module
==============
A Pimlico module consists of a Python package with a special layout. Every module has a file
``info.py``. This contains the definition of the module's metadata: its inputs, outputs, options, etc.

Most modules also have a file ``execute.py``, which defines the routine that's called when it's run. You should take
care when writing ``info.py`` not to import any non-standard Python libraries or have any time-consuming operations
that get run when it gets imported.

``execute.py``, on the other hand, will only get imported when the module is to be run, after dependency checks.

For the example below, let's assume we're writing a module called ``nmf`` and create the following directory structure
for it::

    src/python/myproject/modules/
        __init__.py
        nmf/
            __init__.py
            info.py
            execute.py

Metadata
--------
Module metadata (everything apart from what happens when it's actually run) is defined in ``info.py`` as a class called
``ModuleInfo``.

Here's a sample basic ``ModuleInfo``, which we'll step through.
(It's based on the Scikit-learn :mod:`~pimlico.modules.sklearn.matrix_factorization` module.)

.. code-block:: py

    import json
    from pimlico.core.modules.base import BaseModuleInfo
    from pimlico.datatypes.arrays import ScipySparseMatrix, NumpyArray

    class ModuleInfo(BaseModuleInfo):
        module_type_name = "nmf"
        module_readable_name = "Sklearn non-negative matrix factorization"
        module_inputs = [("matrix", ScipySparseMatrix)]
        module_outputs = [("w", NumpyArray), ("h", NumpyArray)]
        module_options = {
            "components": {
                "help": "Number of components to use for hidden representation",
                "type": int,
                "default": 200,
            },
        }

        def get_software_dependencies(self):
            return super(ModuleInfo, self).get_software_dependencies() + \
                   [PythonPackageOnPip("sklearn", "Scikit-learn")]

The ``ModuleInfo`` should always be a subclass of :class:`~pimlico.core.modules.base.BaseModuleInfo`. There are
some subclasses that you might want to use instead (e.g., see :doc:`/guides/map_module`), but here we just use the
basic one.

Certain class-level attributes should pretty much always be overridden:

- ``module_type_name``: A name used to identify the module internally
- ``module_readable_name``: A human-readable short description of the module
- ``module_inputs``: Most modules need to take input from another module (though not all)
- ``module_outputs``: Describes the outputs that the module will produce, which may then be used as inputs to another module

**Inputs** are given as pairs ``(name, type)``, where ``name`` is a short name to
identify the input and ``type`` is the datatype
that the input is expected to have. Here, and most commonly, this is a subclass of
:class:`~pimlico.datatypes.base.PimlicoDatatype` and Pimlico will check that a dataset supplied for this input is
either of this type, or has a type that is a subclass of this.

Here we take just a single input: a sparse matrix.

**Outputs** are given in a similar way. It is up to the module's executor (see below) to ensure that these outputs
get written, but here we describe the datatypes that will be produced, so that we can use them as input to other
modules.

Here we produce two Numpy arrays, the factorization of the input matrix.

**Dependencies:**
Since we require Scikit-learn to execute this module, we override ``get_software_dependencies()`` to specify this. As
Scikit-learn is available through Pip, this is very easy: all we need to do is specify the Pip package name. Pimlico
will check that Scikit-learn is installed before executing the module and, if not, allow it to be installed
automatically.

Finally, we also define some **options**. The values for these can be specified in the pipeline config file. When the
``ModuleInfo`` is instantiated, the processed options will be available in its ``options`` attribute. So, for example,
we can get the number of components (specified in the config file, or the default of 200) using
``info.options["components"]``.

Executor
--------
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

Skeleton new module
===================
To make developing a new module a little quicker, here's a skeleton module info and executor.

.. code-block:: py

    from pimlico.core.modules.base import BaseModuleInfo

    class ModuleInfo(BaseModuleInfo):
        module_type_name = "NAME"
        module_readable_name = "READABLE NAME"
        module_inputs = [("NAME", REQUIRED_TYPE)]
        module_outputs = [("NAME", PRODUCED_TYPE)]
        # Delete module_options if you don't need any
        module_options = {
            "OPTION_NAME": {
                "help": "DESCRIPTION",
                "type": TYPE,
                "default": VALUE,
            },
        }

        def get_software_dependencies(self):
            return super(ModuleInfo, self).get_software_dependencies() + [
                # Add your own dependencies to this list
                # Remove this method if you don't need to add any
            ]


.. code-block:: py

    from pimlico.core.modules.base import BaseModuleExecutor

    class ModuleExecutor(BaseModuleExecutor):
        def execute(self):
            input_data = self.info.get_input("NAME")
            self.log.info("MESSAGES")

            # DO STUFF

            with SOME_WRITER(self.info.get_absolute_output_dir("NAME")) as writer:
                # Do what the writer requires
