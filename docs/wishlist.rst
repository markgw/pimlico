=====================
  Pimlico Wishlist
=====================

Things I plan to add to Pimlico:

- Handle software dependencies within Python

  - Those that can be installed directly can be installed as part of the pre-run 
    checks
  - Simply output instructions for others (e.g. system-wide install required)

- Further modules:

  - :doc:`CherryPicker <plans/cherry_picker>` for coreference resolution
  - :doc:`Berkeley Parser <plans/berkeley>` for fast constituency parsing
  - :doc:`C&C <plans/candc>` for parsing, tagging, etc
  - OpenNLP coref. I've already wrapper other OpenNLP tools, so this would be pretty easy.
  - `Reconcile <https://www.cs.utah.edu/nlp/reconcile/>`_ coref. Seems to incorporate upstream NLP tasks. Would want
    to interface such that we can reuse output from other modules and just do coref.
  - `Malt dependency parser <http://www.maltparser.org/>`_. I've wrapper this in Python before, so can probably reuse
    that. Faster alternative to CoreNLP dep parser, already wrapped

- Bundle Pimlico Java code as jars, so user doesn't need to compile. Dead easy - just add jar target to ant
  builds and check in resulting jars

*I'll add to this list as I think of things...*
