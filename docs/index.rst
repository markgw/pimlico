=========================
  Pimlico Documentation
=========================

The **Pimlico Processing Toolkit** (PIpelined Modular LInguistic COrpus processing) 
is a toolkit for building pipelines made up of linguistic processing tasks 
to run on large datasets (corpora). It provides a wrappers around many 
existing, widely used NLP (Natural Language Processing) tools. 
It makes it easy to write large, potentially complex pipelines 
with the following key goals:

* to provide **clear documentation** of what has been done;
* to make it easy to **incorporate standard NLP tasks**,
* and to extend the code with **non-standard tasks, specific to a pipeline**;
* to support simple **distribution of code** for reproduction, for example, on other datasets.

The toolkit takes care of managing data between the steps of a 
pipeline and checking that everything's executed in the right order.

.. note::
   *Pimlico is a new project*, so there isn't much documentation yet. 
   I'll be documenting things as I develop them.
   
   The basic framework is up and running, but:
   
   - it doesn't yet include wrappers for many standard NLP tools: I'll be 
     adding these more of less as I need them and am keen to accept contributions 
     of wrappers if you develop them for your own pipelines
   - there are some key features missing, which I'll add as time goes on. 
     See :doc:`wishlist <my wishlist>` for things that I'm currently planning to 
     add.

Contents:

.. toctree::
   :maxdepth: 2


Guides
======
* :doc:`setup_guide`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

