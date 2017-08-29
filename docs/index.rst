=========================
  Pimlico Documentation
=========================

.. image:: logo_p_site.svg
   :width: 150px
   :alt: Pimlico logo
   :align: right
   
The **Pimlico Processing Toolkit** 
is a toolkit for building pipelines of tasks for **processing large datasets** (corpora). 
It is especially focussed on processing linguistic corpora and 
provides wrappers around many
existing, widely used **NLP** (Natural Language Processing) tools.

It makes it easy to write large, potentially complex pipelines 
with the following key goals:

* to provide **clear documentation** of what has been done;
* to make it easy to **incorporate standard NLP tasks**,
* and to extend the code with **non-standard tasks, specific to a pipeline**;
* to support simple **distribution of code** for reproduction, for example, on other datasets.

The toolkit takes care of managing data between the steps of a 
pipeline and checking that everything's executed in the right order.

The core toolkit is written in Python. Pimlico is open source, released under the GPLv3 license. It is
available from `its Github repository <https://github.com/markgw/pimlico>`_.
To get started with a Pimlico project, follow the :doc:`getting-started guide <guides/setup>`.

Pimlico is short for *PIpelined Modular LInguistic COrpus processing*.

More NLP tools will gradually be added. See :doc:`my wishlist <plans/wishlist>` for current plans.

Contents
========

.. toctree::
   :maxdepth: 2

   guides/index
   core/index
   modules/pimlico.modules
   plans/index
   api


* :ref:`genindex`
* :ref:`search`
