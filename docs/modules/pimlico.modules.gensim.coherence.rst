Topic model topic coherence
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.gensim.coherence

+------------+----------------------------------+
| Path       | pimlico.modules.gensim.coherence |
+------------+----------------------------------+
| Executable | yes                              |
+------------+----------------------------------+

Compute topic coherence.

Takes input as a list of the top words for each topic. This can be produced
from various types of topic model, so they can all be evaluated using this method.

Also requires a corpus from which to compute the PMI statistics. This should
typically be a different corpus to that on which the model was trained.

For now, this just computes statistics and outputs them to a text file, and
also outputs a single number representing the mean topic coherence across
topics.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name             | Type(s)                                                                                                                                                                |
+==================+========================================================================================================================================================================+
| topics_top_words | :class:`topics_top_words <pimlico.datatypes.gensim.TopicsTopWords>`                                                                                                    |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| corpus           | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| vocab            | :class:`dictionary <pimlico.datatypes.dictionary.Dictionary>`                                                                                                          |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+----------------+-------------------------------------------------------------------+
| Name           | Type(s)                                                           |
+================+===================================================================+
| output         | :class:`named_file <pimlico.datatypes.files.NamedFile>`           |
+----------------+-------------------------------------------------------------------+
| mean_coherence | :class:`numeric_result <pimlico.datatypes.results.NumericResult>` |
+----------------+-------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_topic_coherence_module]
   type=pimlico.modules.gensim.coherence
   input_topics_top_words=module_a.some_output
   input_corpus=module_a.some_output
   input_vocab=module_a.some_output
   

