=========================
  Pimlico Documentation
=========================

.. image:: _static/logo_p_site.svg
   :width: 150px
   :alt: Pimlico logo
   :align: right
   
The **Pimlico Processing Toolkit** 
is a toolkit for building pipelines of tasks for **processing large datasets** (corpora). 
It is especially focussed on processing linguistic corpora and 
provides wrappers around many
existing, widely used **NLP** (Natural Language Processing) tools.

.. note::

   This is the ``python3`` branch of Pimlico, which adds Python 2-3 compatibility.
   This is a lengthy ongoing process. It's now reasonably functional and I welcome
   people using this branch and reporting bugs (in Python 2 or 3).

   If you want a more stable version of Pimlico, use the ``master`` branch or a
   tagged release.

.. note::

   These are the docs for the **release candidate for v1.0**.

   This brings with it a big project
   to change how datatypes work internally (previously in branch ``datatypes``)
   and requires all datatypes and modules
   to be updated to the new system.
   `More info... <https://github.com/markgw/pimlico/projects/1>`_

   Modules marked with ``!!`` in the docs are waiting to be updated and
   don't work. Other known outstanding tasks are marked with todos:
   :doc:`full todo list </plans/wishlist>`.

   These issues will be resolved before v1.0 is released.

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

Currently, Pimlico only supports **Python 2**.
`Work is underway <https://github.com/markgw/pimlico/issues/8>`_
to make it **Python 3 compatible**, but it's a large and complex
codebase, so this will take some time.

Pimlico is short for *PIpelined Modular LInguistic COrpus processing*.

More NLP tools will gradually be added. See :doc:`my wishlist <plans/wishlist>` for current plans.

Contents
========

.. toctree::
   :maxdepth: 1
   :titlesonly:

   guides/index
   core/index
   modules/pimlico.modules
   commands/index
   api
   test_config/index
   plans/index


* :ref:`genindex`
* :ref:`search`
