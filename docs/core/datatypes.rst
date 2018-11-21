=============
  Datatypes
=============

A core concept in Pimlico is the *datatype*. All inputs and outputs to
modules are associated with a datatype and typechecking ensures that
outputs from one module are correctly matched up with inputs to the next.

Datatypes also provide interfaces for reading and writing datasets. They provide different
ways of reading in or iterating over datasets and different ways to write out datasets,
as appropriate to the datatype. They are used by Pimlico to typecheck connections
between modules to make sure that the output from one module provides a suitable
type of data for the input to another. They are then also used by the modules to read
in their input data coming from earlier in a pipeline and to write out their output
data, to be passed to later modules.

As much as possible, Pimlico pipelines should use :mod:`standard datatypes <pimlico.datatypes>`
to connect up the output of modules
with the input of others. Most datatypes have a lot in common,
which should be reflected in their sharing
common base classes. **Input modules** take care of reading in data from external sources
and they provide access to that data in a way that is identified by a Pimlico datatype.

Class structure
===============

Instances of subclasses of :class:`~pimlico.datatypes.base.PimlicoDatatype` represent the type of datasets
and are used for typechecking in a pipeline.
Each datatype has an associated ``Reader`` class, accessed by ``datatype_cls.Reader``.
These are created automatically and can be instantiated via the datatype instance (by calling it).
They are all subclasses of :class:`~pimlico.datatypes.base.PimlicoDatatype` ``.Reader``.

It is these readers that are used within a pipeline to read a dataset output by an earlier
module. In some cases, other readers may be used: for example, input modules provide
standard datatypes at their outputs, but use special readers to provide access to
the external data via the same interface as if the data had been stored within the pipeline.

A similar reflection of the datatype hierarchy is used for **dataset writers**, which are
used to write the outputs from modules, to be passed to subsequent modules. These
are created automatically, just like readers, and are all subclasses of
:class:`~pimlico.datatypes.base.PimlicoDatatype` ``.Writer``. You can get a datatype's standard writer class
via ``datatype_cls.Writer``. Some datatypes might not provide a writer, but
most do.

Note that you do not need to subclass or instantiate ``Reader``, ``Writer`` or ``Setup``
classes yourself: subclasses are created automatically
to correspond to each reader type. You can, however, add functionality to any of them
by defining a nested class of the same name. It will automatically inherit from
the parent datatype's corresponding class.

Readers
=======

Most of the time, you don't need to worry about the process of getting hold of a
reader, as it is done for you by the module. From within a module executor, you
will usually do this:

.. code-block:: py

   reader = self.info.get_input("input_name")

``reader`` is an instance of the datatype's ``Reader`` class,
or some other reader class providing the same interface. You can
use it to access the data, for example, iterating over a corpus,
or reading in a file, depending on the datatype.

The follow guides describe the process that goes on internally
in more detail.

Reader creation
---------------
The process of instantiating a reader for a given datatype is as follows:

1. Instantiate the datatype. A datatype instance is always associated with
   a module input (or output), so you rarely need to do this explicitly.
2. Use the datatype to instantiate a **reader setup**, by calling it.
3. Use the reader setup to check that the data is ready to reader by calling
   ``ready_to_read()``.
4. If the data is ready, use the reader setup to instantiate a reader, by
   calling it.

Reader setup
------------

Reader setup classes provide any functionality relating to a reader needed
before it is ready to read and instantiated. Like readers and writers,
they are created automatically, so every ``Reader`` class has a ``Setup``
nested class.

Most importantly, the setup instance provides the ``ready_to_read()``
method, which indicates whether the reader is ready to be instantiated.

The standard implementation, which can be used in almost all cases,
takes a list of possible paths to the dataset at initialization and checks
whether the dataset is ready to be read from any of them. You generally
don't need to override ``ready_to_read()`` with this, but just
``data_ready(path)``, which checks whether the data is ready to be read in a
specific location. You can call the parent class' data-ready checks
using super: ``super(MyDatatype.Reader.Setup, self).data_ready(path)``.

The whole ``Setup`` object will
be passed to the corresponding ``Reader``'s init, so that it has access to
data locations, etc. It can then be accessed as ``reader.setup``.

Subclasses may take different init args/kwargs and store whatever attributes
are relevant for preparing their corresponding ``Reader``. In such cases, you
will usually override a ``ModuleInfo``'s ``get_output_reader_setup()`` method
for a specific output's reader preparation, to provide it with the appropriate
arguments. Do this by calling the ``Reader`` class' ``get_setup(*args, **kwargs)``
class method, which passes args and kwargs through to the ``Setup``'s init.

You can add functionality to a reader's setup by creating a
nested ``Setup`` class. This will inherit from the parent reader's setup. This happens
automatically – you don't need to do it yourself and shouldn't
inherit from anything. For example:

.. code-block:: py

   class MyDatatype(PimlicoDatatype):
       class Reader:
           # Overide reader things here

           class Setup:
               # Override setup things here
               # E.g.:
               def data_ready(path):
                   # Parent checks: usually you want to do this
                   if not super(MyDatatype.Reader.Setup, self).data_ready(path):
                       return False
                   # Check whether the data's ready according to our own criteria
                   # ...
                   return True

Instantiate a reader setup of the relevant type by calling the
datatype. Args and kwargs will be
passed through to the ``Setup`` class' init. They may depend on the particular
setup class, but typically one arg is required, which is a list of paths
where the data may be found.

Reader from setup
-----------------

You can use the reader setup to get a reader, once the data is ready to
read.

This is done by simply calling the setup, with the pipeline instance as the
first argument and, optionally, the name of the module that's currently
being run. (If given, this will be used in error output, debugging, etc.)

The procedure then looks something like this:

.. code-block:: py

   datatype = ThisDatatype(options...)
   # Most of the time, you will pass in a list of possible paths to the data
   setup = datatype(possible_paths_list)
   # Now check whether the data is ready to read
   if setup.ready_to_read():
       reader = setup(pipeline, module="pipeline_module")


Creating a new datatype
=======================

This is the typical process for creating a new datatype. Of course, some datatypes do more, and
some of the following is not always necessary, but it's a good guide for reference.

1. Create the datatype class, which may subclass :class:`~pimlico.datatypes.base.PimlicoDatatype` or some other existing
   datatype.
2. Specify a ``datatype_name`` as a class attribute.
3. Specify software dependencies for reading the data, if any, by overriding ``get_software_dependencies()``
   (calling the super method as well).
4. Specify software dependencies for writing the data, if any that are not among the reading dependencies,
   by overriding ``get_writer_software_dependencies()``.
5. Define a nested ``Reader`` class to add any methods to the reader for this datatype. The data should
   be read from the directory given by its ``data_dir``. It should provide methods for getting different
   bits of the data, iterating over it, or whatever is appropriate.
6. Define a nested ``Setup`` class within the reader with a ``data_ready(base_dir)`` method to check whether the
   data in ``base_dir`` is ready to be read using the reader.
   If all that this does is check the existence of particular filenames or paths within the data
   dir, you can instead implement the ``Setup`` class' ``get_required_paths()`` method to return the
   paths relative to the data dir.
7. Define a nested ``Writer`` class in the datatype to add any methods to the writer for this datatype.
   The data should be written to the path given by its ``data_dir``. Provide methods that the user can
   call to write things to the dataset. Required elements of the dataset should be specified as a list of
   strings as the ``required_tasks`` attribute and ticked off as written using ``task_complete()``
8. You may want to specify:

   * ``datatype_options``: an OrderedDict of option definitions
   * ``shell_commands``: a list of shell commands associated with the datatype


Defining reader functionality
-----------------------------

Naturally, different datatypes provide different ways to access their data.
You do this by (implicitly) overriding the datatype's ``Reader`` class and
adding methods to it.

As with ``Setup`` and ``Writer`` classes, you do not need to subclass the
``Reader`` explicitly yourself: subclasses are created automatically
to correspond to each datatype. You add functionality to a datatype's reader by creating a
nested ``Reader`` class, which inherits from the parent datatype's reader. This happens
automatically – your nested class shouldn't inherit from anything:

.. code-block:: py

   class MyDatatype(PimlicoDatatype):
       class Reader:
           # Override reader things here
           def get_some_data(self):
               # Do whatever you need to do to provide access to the dataset
               # You probably want to use the attribute 'data_dir' to retrieve files
               # For example:
               with open(os.path.join(self.data_dir, "my_file.txt")) as f:
                   some_data = f.read()
               return some_data
