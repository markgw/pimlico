=======================
Introduction to Pimlico
=======================

Motivation
==========
It is becoming more and more common for conferences and journals in NLP and other
computational areas to encourage, or even require, authors to make publicly
available the code and data required to reproduce their reported results. It is
now widely acknowledged that such practices lie at the center of open science
and are essential to ensuring that
research contributions are verifiable, extensible and useable in applications.

However, this requires extensive additional work. And,
even when researchers do this, it is all too common for others
to have to spend large amounts of time and effort preparing data, downloading
and installing tools, configuring execution environments and picking through
instructions and scripts before they can reproduce the original results, never mind
apply the code to new datasets or build upon it in novel research.

Introducing Pimlico
===================
Pimlico (**Pi**\ pelined **M**\ odular **Li**\ nguistic **Co**\ rpus processing) addresses these problems.
It allows users to write and run potentially complex processing pipelines, with
the key goals of making it easy to:

  - clearly document what was done;
  - incorporate standard NLP and data-processing tasks with minimal effort;
  - integrate non-standard code, specific to the task at hand, into the same pipeline; and
  - distribute code for later reproduction or application to other datasets or experiments.

It comes with pre-defined **module types** to wrap a number of existing **NLP toolkits**
(including non-Python code) and carry out many other common pre-processing or
data manipulation tasks.

Building pipelines
==================
Pimlico addresses the task of **building of pipelines to process large datasets**.
It allows you to run one or several steps of
processing at a time, with high-level control over how each step is run,
manages the data produced by each step,
and lets you observe these intermediate outputs.
Pimlico provides simple, powerful
tools to give this kind of control, without needing to write any code.

Developing a pipeline with Pimlico involves defining the **structure of the pipeline**
itself in terms of **modules** to be executed, and
**connections between their inputs and outputs** describing the flow of data.

Modules correspond to some data-processing code, with some parameters.
They may be of a standard type, so-called **core module types**, for which
code is provided as part of Pimlico.

A pipeline may also incorporate
**custom module types**, for which metadata and data-processing code must be
provided by the author.

Pipeline configuration
======================

   See :doc:`/core/config` for more on pipeline configuration.


At the heart of Pimlico is the concept of a **pipeline configuration**, defined
by a configuration (or *conf*) file,
which can be loaded and executed.

This specifies
some general parameters and metadata regarding the pipeline and then a sequence of
modules to be executed.

Each **pipeline module** is defined by a named section in
the file, which specifies the module type, inputs to be read from the outputs
of other, previous modules, and parameters.

For example, the following configuration section defines
a module called ``split``. Its type is the core Pimlico module
type :mod:`corpus split <pimlico.modules.corpora.split>`,
which splits a corpus by documents
into two randomly sampled subsets (as is typically done to produce training
and test sets).

.. code-block:: ini

   [split]
   type=pimlico.modules.corpora.split
   input=tokenized_corpus
   set1_size=0.8

The option ``input`` specifies where the
module's only input comes from and refers by name to a module defined
earlier in the pipeline whose output provides the data.
The option ``set1_size`` tells the module
to put 80% of documents into the first set and 20% in the second. Two
outputs are produced, which can be referred to later in the pipeline as
``split.set1`` and ``split.set2``.

Input modules
-------------
The first module(s) of a pipeline have no inputs, but load datasets,
with parameters to specify where the input data can be found on the filesystem.

A number of :mod:`standard input readers <pimlico.modules.input>`
are among Pimlico's core module types to
support reading of simple datasets, such as text files in a directory, and
some standard input formats for data such as word embeddings. The toolkit
also provides a factory to make it easy to define custom
routines for reading other types of input data.

Module type
-----------
The **type** of a module is given as a fully qualified Python path to a
Python package.

The package provides separately the module type's metadata,
referred to as its *module info* –
input datatypes, options, etc. – and the code that is executed when
it is run, the *module executor*.
The example above uses one of
Pimlico's core module types.

A pipeline will
usually also include non-standard module types, distributed
together with the conf file. These are defined and used in exactly
the same way as the core module types.
Where custom module types are used, the pipeline conf file specifies a directory
where the source code can be found.

.. seealso:: :doc:`Full worked example </example_config/simple.custom_module>`

   An example of a complete pipeline conf, using both core and
   custom module types



Datatypes
=========

When a module is run, its output is
stored ready for use by subsequent modules. Pimlico takes care
of storing each module's output in separate locations and providing the
correct data as input.

The module info for a module type defines a **datatype**
for each input and each output.
Pimlico includes a system of datatypes for the datasets
that are passed between modules.

When a pipeline is loaded, type-checking is performed on
the connections between modules' outputs and subsequent modules' inputs to
ensure that appropriate datatypes are provided.

For example, a module may
require as one of its inputs a vocabulary, for which Pimlico provides a
:class:`standard datatype <pimlico.datatypes.dictionary.Dictionary>`.
The pipeline will only be loaded if this input is
connected to an output that supplies a compatible type. The supplying
module does not need to define how to store a vocabulary, since the datatype
defines the necessary routines for **writing a vocabulary to disk**. The
subsequent module does not need to define how to **read the data** either, since
the datatype takes care of that too, providing the module executor
with suitable Python data structures.

Corpora
-------
Often modules read and write **corpora**, consisting of a large number
of documents. Pimlico provides a datatype for representing such corpora and
a further type system for the **types of the documents**
stored within a corpus
(rather like Java's *generic* types).

For example, a module may
specify that it requires as input a corpus whose documents contain
tokenized text. All tokenizer modules (of which there are several)
provide output corpora with this document type. The corpus
datatype takes care of reading and writing large
corpora, preserving the order of documents, storing corpus metadata, and
much more.

The datatype system is also extensible in custom code. As well
as defining custom module types, a pipeline author may wish to define new
datatypes to represent the data required as
input to the modules or provided as output.

.. seealso::

   :class:`~pimlico.datatypes.corpora.base.IterableCorpus`: datatype for corpora.


Running a pipeline
==================

Pimlico provides a command-line interface for parsing and executing
pipelines. The interface provides sub-commands to
perform different operations relating to a given pipeline.
The conf file defining the pipeline is always given as
an argument and the first operation is therefore to parse the
pipeline and check it for validity.
We describe here a few of the most important sub-commands.

.. seealso:: :doc:`/commands/index`

   A complete list of the available commands

status
------
   :doc:`The status subcommand </commands/status>`

Outputs a list of all of the modules in the pipeline,
reporting the execution status of each. This indicates whether the
module has been run; if so, whether it completed successfully or
failed; if not, whether it is ready to be run (i.e. all of its
input data is available).

Each of the modules is numbered in the list, and this number can
be used instead of the module's full name in arguments to all
sub-commands.

Given the name of a module, the command outputs a detailed
report on the status of that module and its input and output datasets.

run
---
   :doc:`The run subcommand </commands/run>`

Executes a module.

An option ``--dry`` runs all pre-execution
checks for the module, without running it. These include checking
that required software is installed
and performing automatic installation if not.

If all requirements are satisfied, the module will be executed, outputting
its progress to the terminal and to module-specific log files. Output datasets
are written to module-specific directories, ready to be used by subsequent
modules later.

Multiple modules can be run in sequence, or even the entire
pipeline. A switch ``--all-deps`` causes any unexecuted modules upon
whose output the specified module(s) depend to be run.

browse
------
   :doc:`The browse subcommand </commands/browse>`

Inspects the data output by a module,
stored in its pipeline-internal storage. Inspecting output data by
loading the files output by the module would require
knowledge of both the Pimlico data storage system and the specific storage
formats used by the output datatypes. Instead,
this command lets the user inspect the data from
a given module (and a given output, if there are multiple).

Datatypes, as part of their definition, along with specification of storage
format reading and writing, define how the data can be
formatted for display.
Multiple formatters may be defined, giving alternative ways to inspect the same data.

For some datatypes, browsing is as simple as outputting some statistics
about the data, or a string representing its contents. For corpora, a
document-by-document browser is provided, using the `Urwid <http://urwid.org/>`_
library. Furthermore, the definition of corpus document types
determines how an individual document should be
displayed in the corpus browser. For example, the tokenized text type shows
each sentence on a separate line, with spaces between tokens.

Where next?
===========

For a practical quick-start guide to building pipelines, see :doc:`fast_setup`.

Or for a bit more detail, see :doc:`setup`.