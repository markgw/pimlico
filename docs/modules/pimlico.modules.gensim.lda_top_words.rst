LDA top words
~~~~~~~~~~~~~

.. py:module:: pimlico.modules.gensim.lda_top_words

+------------+--------------------------------------+
| Path       | pimlico.modules.gensim.lda_top_words |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Extract the top words for each topic from a Gensim LDA model.

Can be used as input to coherence evaluation.

Currently, this just outputs the highest probability words, but it
could be extended in future to extract words according to other measures,
like `relevance or lift <https://nlp.stanford.edu/events/illvi2014/papers/sievert-illvi2014.pdf>`_.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+-------+--------------------------------------------------------------+
| Name  | Type(s)                                                      |
+=======+==============================================================+
| model | :class:`lda_model <pimlico.datatypes.gensim.GensimLdaModel>` |
+-------+--------------------------------------------------------------+

Outputs
=======

+-----------+---------------------------------------------------------------------+
| Name      | Type(s)                                                             |
+===========+=====================================================================+
| top_words | :class:`topics_top_words <pimlico.datatypes.gensim.TopicsTopWords>` |
+-----------+---------------------------------------------------------------------+


Options
=======

+-----------+------------------------------------------------+------+
| Name      | Description                                    | Type |
+===========+================================================+======+
| num_words | Number of words to show per topic. Default: 15 | int  |
+-----------+------------------------------------------------+------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_lda_top_words_module]
   type=pimlico.modules.gensim.lda_top_words
   input_model=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_lda_top_words_module]
   type=pimlico.modules.gensim.lda_top_words
   input_model=module_a.some_output
   num_words=15

