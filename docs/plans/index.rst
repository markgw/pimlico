============
Future plans
============

Development of Pimlico is constantly ongoing. A lot of this involves adding
new :mod:`core module types <pimlico.modules>`. There are also planned
feature enhancements.

Wishlist
========

Things I plan to add to Pimlico.

- :doc:`Pipeline graph visualizations <drawing>`. Maybe an interactive GUI to help with viewing large pipelines
- Model fetching: system like software dependency checking and installation to download models on demand
- See `issue list on Github <https://github.com/markgw/pimlico/issues>`_ for other specific plans

**Module types to be updated**, implemented in the old datatypes system (using backwards incompatible library
features). These do not take long to update and include in the main library.

- C&C parser
- CoreNLP tools (switch to using Stanza wrappers, see below)
- Compiling term-feature matrices (for count-based embeddings among other things)
- Building count-based embeddings from dependency features
- OpenNLP tools. Some already updated. To do:

  * Coreference resolution
  * Coreference pipeline (from raw text)
  * NER

- R-script: simple module to run an arbitrary R script
- Scikit-learn matrix factorization. (Lots of Scikit-learn modules could be added, but this one already exists in an old form.)
- Copy file utility: output a file to a given location outside the pipeline-internal storage
- Bar chart visualization

**New module types**

- Stanza tools: Stanford's new toolkit, includes Python bindings and CoreNLP wrappers
- More spaCy tools: currently only have tokenizer

**More details** on some of these plans

.. toctree::
   :maxdepth: 2

   berkeley
   cherry_picker
   drawing

Todos
=====
The following to-dos appear elsewhere in the docs. They are generally bits of the documentation I've not written
yet, but am aware are needed.

.. todolist::
