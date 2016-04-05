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
- Reconsider TarredCorpus as the common dataset format. There's no obvious advantage over just grouping documents
  in directories, which has the advantage of allowing freer parallelization. However, this might run into filesystem
  trouble where there's a very large number of docs in a corpus (many inodes in subdirectories)
- Or consider parallelizing at the archive level: allow TarredCorpus to iterate over specific archives, then send
  each archive off to be processed in parallel, meaning we can write files linearly within an archive, but have many
  (roughly equally sized) archives going at once

*I'll add to this list as I think of things...*
