GloVe embedding reader \(Gensim\)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.embeddings.glove

+------------+----------------------------------------+
| Path       | pimlico.modules.input.embeddings.glove |
+------------+----------------------------------------+
| Executable | yes                                    |
+------------+----------------------------------------+

Reads in embeddings from the `GloVe <https://nlp.stanford.edu/projects/glove/>`_ format, storing
them in the format used internally in Pimlico for embeddings. We use Gensim's implementation
of the format reader, so the module depends on Gensim.

Can be used, for example, to read the pre-trained embeddings
`offered by Stanford <https://nlp.stanford.edu/projects/glove/>`_.

Note that the format is almost identical to `word2vec`'s text format.

Note that this requires a recent version of Gensim, since they changed their KeyedVectors
data structure. This is not enforced by the dependency check, since we're not able
to require a specific version yet.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

No inputs

Outputs
=======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+


Options
=======

+------+---------------------------------------------+--------+
| Name | Description                                 | Type   |
+======+=============================================+========+
| path | (required) Path to the GloVe embedding file | string |
+------+---------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_glove_embedding_reader_module]
   type=pimlico.modules.input.embeddings.glove
   path=value

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-input-glove.conf`

