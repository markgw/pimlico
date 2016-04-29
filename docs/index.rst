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
   *Pimlico is a new project*, and documentation is taking shape, but still sparse.
   
   There are some key features missing, which I'll add over time, and more NLP tools will gradually be added.
   See :doc:`my wishlist <plans/wishlist>` for current plans.

Contents
========

.. toctree::
   :maxdepth: 2

   guides/index
   core/index
   modules/pimlico.modules
   plans/index


* :ref:`genindex`
* :ref:`API docs <modindex>`
* :ref:`search`
