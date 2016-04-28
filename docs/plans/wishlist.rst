=====================
  Pimlico Wishlist
=====================

Things I plan to add to Pimlico.

- Handle software dependencies within Python

  - Those that can be installed directly can be installed as part of the pre-run checks
  - Simply output instructions for others (e.g. system-wide install required)

- Further modules:

  - :doc:`CherryPicker <cherry_picker>` for coreference resolution
  - :doc:`Berkeley Parser <berkeley>` for fast constituency parsing
  - `Reconcile <https://www.cs.utah.edu/nlp/reconcile/>`_ coref. Seems to incorporate upstream NLP tasks. Would want
    to interface such that we can reuse output from other modules and just do coref.
  - Caevo: :mod:`partially implemented <pimlico.modules.caevo>`

- Output pipeline graph visualizations: :doc:`drawing`
- Bug in counting of corpus size (off by one) when a map process restarts

Todos
=====

.. todolist::
