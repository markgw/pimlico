Annotated text
~~~~~~~~~~~~~~


.. py:module:: pimlico.modules.input.text_annotations


Datasets that store text with accompanying annotations, like POS tags or dependency parses.

There are lots of different ways of storing this type of data in common usage. Here we currently
only implement variants on one -- the VRT format, used by Korp. In future, others should be
added, e.g. CoNLL dependency parses.

Datatypes exist for some of these, which should be converted to input readers in due course.



.. toctree::
   :maxdepth: 2
   :titlesonly:

   pimlico.modules.input.text_annotations.vrt
   pimlico.modules.input.text_annotations.vrt_text
