fastText embedding trainer
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.fasttext

+------------+-------------------------------------+
| Path       | pimlico.modules.embeddings.fasttext |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Train fastText embeddings on a tokenized corpus.

Uses the `fastText Python package <https://fasttext.cc/docs/en/python-module.html>`.

FastText embeddings store more than just a vector for each word, since they
also have sub-word representations. We therefore store a standard embeddings
output, with the word vectors in, and also a special fastText embeddings output.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                |
+======+========================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------------+--------------------------------------------------------------------------------+
| Name       | Type(s)                                                                        |
+============+================================================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>`                  |
+------------+--------------------------------------------------------------------------------+
| model      | :class:`fasttext_embeddings <pimlico.datatypes.embeddings.FastTextEmbeddings>` |
+------------+--------------------------------------------------------------------------------+


Options
=======

+----------------+----------------------------------------------------------------+--------------------------------+
| Name           | Description                                                    | Type                           |
+================+================================================================+================================+
| bucket         | number of buckets. Default: 2,000,000                          | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| dim            | size of word vectors. Default: 100                             | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| epoch          | number of epochs. Default: 5                                   | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| loss           | loss function: ns, hs, softmax, ova. Default: ns               | 'ns', 'hs', 'softmax' or 'ova' |
+----------------+----------------------------------------------------------------+--------------------------------+
| lr             | learning rate. Default: 0.05                                   | float                          |
+----------------+----------------------------------------------------------------+--------------------------------+
| lr_update_rate | change the rate of updates for the learning rate. Default: 100 | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| maxn           | max length of char ngram. Default: 6                           | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| min_count      | minimal number of word occurences. Default: 5                  | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| minn           | min length of char ngram. Default: 3                           | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| model          | unsupervised fasttext model: cbow, skipgram. Default: skipgram | 'skipgram' or 'cbow'           |
+----------------+----------------------------------------------------------------+--------------------------------+
| neg            | number of negatives sampled. Default: 5                        | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| t              | sampling threshold. Default: 0.0001                            | float                          |
+----------------+----------------------------------------------------------------+--------------------------------+
| verbose        | verbose. Default: 2                                            | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| word_ngrams    | max length of word ngram. Default: 1                           | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+
| ws             | size of the context window. Default: 5                         | int                            |
+----------------+----------------------------------------------------------------+--------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_fasttext_module]
   type=pimlico.modules.embeddings.fasttext
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_fasttext_module]
   type=pimlico.modules.embeddings.fasttext
   input_text=module_a.some_output
   bucket=2000000
   dim=100
   epoch=5
   loss=ns
   lr=0.05
   lr_update_rate=100
   maxn=6
   min_count=5
   minn=3
   model=skipgram
   neg=5
   t=0.00
   verbose=2
   word_ngrams=1
   ws=5

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-embeddings-fasttext.conf`

