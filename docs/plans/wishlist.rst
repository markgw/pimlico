=====================
  Pimlico Wishlist
=====================

Things I plan to add to Pimlico.
I'll add to this list as I think of things...

- Handle software dependencies within Python

  - Those that can be installed directly can be installed as part of the pre-run 
    checks
  - Simply output instructions for others (e.g. system-wide install required)

- Further modules:

  - :doc:`CherryPicker <cherry_picker>` for coreference resolution
  - :doc:`Berkeley Parser <berkeley>` for fast constituency parsing
  - :doc:`C&C <candc>` for parsing, tagging, etc
  - OpenNLP coref. I've already wrapper other OpenNLP tools, so this would be pretty easy.
  - `Reconcile <https://www.cs.utah.edu/nlp/reconcile/>`_ coref. Seems to incorporate upstream NLP tasks. Would want
    to interface such that we can reuse output from other modules and just do coref.
  - `Malt dependency parser <http://www.maltparser.org/>`_. I've partially wrapped this in Python before, so can probably reuse
    that. Faster alternative to CoreNLP dep parser (already wrapped)

- Consider parallelizing at the (tar) archive level: allow TarredCorpus to iterate over specific archives, then send
  each archive off to be processed in parallel, meaning we can write files linearly within an archive, but have many
  (roughly equally sized) archives going at once
- Output pipeline graph visualizations: :doc:`drawing`
- Parallelization should only be allowed for the actual module being executed, never for filter modules. If filters
  parallelize, we end up with more processes than we asked for!
- Something odd's going on with restarting halfway through when there's a filter module. The final modules doesn't
  seem to recognize that it's restarting, while the filter module finishes before the final module does...
