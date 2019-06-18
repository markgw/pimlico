Document\-level text filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. py:module:: pimlico.modules.text


Simple text filters that are applied at the document level, i.e. each document in a TarredCorpus
is processed one at a time. These perform relatively simple processing, not relying on external
software or involving lengthy processing times. They are therefore most often used using the
``filter=T`` option, so that the processing is performed on the fly.

Such filters are needed sometimes just to convert before different datapoint formats.

Probably a good deal of these will be added in due course.



.. toctree::
   :maxdepth: 2
   :titlesonly:

   pimlico.modules.text.char_tokenize
   pimlico.modules.text.normalize
   pimlico.modules.text.simple_tokenize
   pimlico.modules.text.text_normalize
   pimlico.modules.text.untokenize
