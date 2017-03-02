=====================
  Pimlico Wishlist
=====================

Things I plan to add to Pimlico.

- Further modules:

  - :doc:`CherryPicker <cherry_picker>` for coreference resolution
  - :doc:`Berkeley Parser <berkeley>` for fast constituency parsing
  - `Reconcile <https://www.cs.utah.edu/nlp/reconcile/>`_ coref. Seems to incorporate upstream NLP tasks. Would want
    to interface such that we can reuse output from other modules and just do coref.

- **Pipeline graph visualizations**: :doc:`drawing`. Maybe an interactive GUI to help with viewing large pipelines
- **Email output**: after a run finishes, successful or failed, send an email (if configured to do so) reporting the
    status. This would mean you could be informed immediately if something goes wrong and the pipeline exits early,
    or if everything completes and your output is ready.

Todos
=====
The following to-dos appear elsewhere in the docs. They are generally bits of the documentation I've not written
yet, but am aware are needed.

.. todolist::
