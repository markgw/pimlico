OpenNLP tools
~~~~~~~~~~~~~


.. py:module:: pimlico.modules.opennlp


A collection of module types to wrap individual OpenNLP tools.

At the moment, this includes several tool. A few other modules have been
here previously, but have not yet been updated to the new datatypes system.
See :mod:`pimlico.old_datatypes.modules.opennlp`.

Other OpenNLP tools can be wrapped fairly straightforwardly following the same
pattern, using Py4J.



.. toctree::
   :maxdepth: 2
   :titlesonly:

   pimlico.modules.opennlp.parse
   pimlico.modules.opennlp.pos
   pimlico.modules.opennlp.tokenize
