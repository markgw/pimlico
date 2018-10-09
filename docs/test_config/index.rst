.. _test-pipelines:

Module test pipelines
~~~~~~~~~~~~~~~~~~~~~

Test pipelines provide a special sort of unit testing for Pimlico.

Pimlico is distributed with a set of test pipeline config files, each just a 
small pipeline with a couple of modules in it. Each is designed to test the 
use of a particular one of Pimlico's builtin module types, or some combination 
of a smaller number of them.

Available pipelines
===================

.. toctree::
   :maxdepth: 2
   :titlesonly:

   text.normalize.conf.rst
   text.simple_tokenize.conf.rst
   input.raw_text_files.conf.rst
   input.fasttext.conf.rst
   input.glove.conf.rst
   opennlp.tokenize.conf.rst
   corpora.store.conf.rst
   corpora.concat.conf.rst
   corpora.group.conf.rst
   corpora.vocab_builder.conf.rst
   corpora.subset.conf.rst
   corpora.interleave.conf.rst
   corpora.stats.conf.rst
   corpora.list_filter.conf.rst
   corpora.split.conf.rst


Input data
==========

Pimlico also comes with all the data necessary to run the pipelines. They 
all use very small datasets, so that they don't take long to run and can 
be easily distributed. 

Some of the datasets are raw data, of the sort you 
might find in a distributed corpus, and these are used to test input readers 
for that type of data. Most, however, are stored in one of Pimlico's datatype 
formats, exactly as they were output from some other module (most often 
from another test pipeline), so that they can be read in to test one 
module in isolation.

Usage examples
==============

In addition to providing unit testing for core Pimlico modules, test pipelines 
also function as a source of examples of each module's usage. They are for 
that reason linked to from the module's documentation, so that example usages 
can be easily found where available.

Running
=======

To run test pipelines, you can use the script ``test_pipeline.sh`` in Pimlico's 
bin directory, e.g.:

.. code-block:: sh
   
   ./test_pipeline.sh ../test/data/pipelines/corpora/concat.conf output

This will load a single test pipeline from the given config file and execute 
the module named ``output``.

There are also some suites of tests, specified as CSV files giving a number 
of config files and module names to execute for each. To run the main suite 
of test pipelines for Pimlico's core modules, run:

.. code-block:: sh
   
   ./all_test_pipelines.sh

