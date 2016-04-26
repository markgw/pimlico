Pimlico module: C&C parser
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.candc

+------------+-----------------------+
| Path       | pimlico.modules.candc |
+------------+-----------------------+
| Executable | yes                   |
+------------+-----------------------+

Wrapper around the original `C&C parser <http://svn.ask.it.usyd.edu.au/trac/candc/>`_.

Takes tokenized input and parses it with C&C. The output is written exactly as it comes out from C&C.
It contains both GRs and supertags, plus POS-tags, etc.

The wrapper uses C&C's SOAP server. It sets the SOAP server running in the background and then calls C&C's
SOAP client for each document. If parallelizing, multiple SOAP servers are set going and each one is kept
constantly fed with documents.


Inputs
======

+-----------+------------------------------------------------------------------------+
| Name      | Type(s)                                                                |
+===========+========================================================================+
| documents | :class:`TokenizedCorpus <pimlico.datatypes.tokenized.TokenizedCorpus>` |
+-----------+------------------------------------------------------------------------+

Outputs
=======

+--------+------------------------------------------------------------------------------+
| Name   | Type(s)                                                                      |
+========+==============================================================================+
| parsed | :class:`CandcOutputCorpus <pimlico.datatypes.parse.candc.CandcOutputCorpus>` |
+--------+------------------------------------------------------------------------------+

Options
=======

+-------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                                                                                                         | Type   |
+=======+=====================================================================================================================================================================================================================+========+
| model | Absolute path to models directory or name of model set. If not an absolute path, assumed to be a subdirectory of the candcs models dir (see instructions in models/candc/README on how to fetch pre-trained models) | string |
+-------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

