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

   gensim.dtm_train.conf.rst
   gensim.dtm_infer.conf.rst
   opennlp.tokenize.conf.rst
   opennlp.parse.conf.rst
   opennlp.pos.conf.rst
   embeddings.normalize.conf.rst
   embeddings.word2vec.conf.rst
   embeddings.store_word2vec.conf.rst
   embeddings.store_tsv.conf.rst
   embeddings.fasttext.conf.rst
   corpora.interleave.conf.rst
   corpora.list_filter.conf.rst
   corpora.vocab_unmapper.conf.rst
   corpora.shuffle_linear.conf.rst
   corpora.subset.conf.rst
   corpora.concat.conf.rst
   corpora.subsample.conf.rst
   corpora.vocab_builder.conf.rst
   corpora.group.conf.rst
   corpora.split.conf.rst
   corpora.vocab_mapper.conf.rst
   corpora.store.conf.rst
   corpora.stats.conf.rst
   corpora.filter_tokenize.conf.rst
   corpora.vocab_mapper_longer.conf.rst
   corpora.vocab_counter.conf.rst
   corpora.shuffle.conf.rst
   corpora.formatters.tokenized.conf.rst
   text.simple_tokenize.conf.rst
   text.normalize.conf.rst
   text.text_normalize.conf.rst
   text.char_tokenize.conf.rst
   input.europarl.conf.rst
   input.raw_text_files.conf.rst
   input.xml.conf.rst
   input.glove.conf.rst
   input.fasttext.conf.rst
   spacy.tokenize.conf.rst
   utility.collect_files.conf.rst
   nltk.nist_tokenize.conf.rst
   malt.parse.conf.rst
   visualization.embeddings_plot.conf.rst
   core.filter_map.conf.rst


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


