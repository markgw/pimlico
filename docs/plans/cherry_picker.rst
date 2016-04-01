=============
Cherry Picker
=============

**Coreference resolver**

http://www.hlt.utdallas.edu/~altaf/cherrypicker/

Requires NER, POS tagging and constituency parsing to be done first. Tools for all of these are included in the
Cherry Picker codebase, but we just need a wrapper around the Cherry Picker tool itself to be able to feed these
annotations in from other modules and perform coref.

Write a Java wrapper and interface with it using Py4J, as with OpenNLP.
