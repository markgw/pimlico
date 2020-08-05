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

It makes it easy to write large, potentially complex pipelines 
with the key goals of making is easy to:

* provide **clear documentation** of what has been done;
* **incorporate standard NLP tasks** and data-processing tasks with minimal effort;
* **integrate non-standard code**, specific to the task at hand, into the same pipeline; and
* **distribute code** for later reproduction or application to other datasets or experiments.

The toolkit takes care of managing data between the steps of a 
pipeline and checking that everything's executed in the right order.

The core toolkit is written in Python. Pimlico is open source, released under the GPLv3 license. It is
available from `its Github repository <https://github.com/markgw/pimlico>`_.
To get started with a Pimlico project, follow the :doc:`getting-started guide <guides/setup>`.

Pimlico is written in Python and can be run using Python >=2.7 or >=3.6. This means
you can write your own processing modules using either Python 2 or 3.

Pimlico is short for *PIpelined Modular LInguistic COrpus processing*.

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
   example_config/index
   plans/index


.. note::

   **New datatypes system**

   Some time ago, we changed how datatypes work internally, requiring
   all datatypes and modules to be updated.
   `More info... <https://github.com/markgw/pimlico/projects/1>`_

   This has been done for many of the core modules, but some are waiting
   to be updated and
   don't work. They do not appear in the documentation and can
   be found in ``pimlico.old_datatypes.modules``.

   These issues will be resolved before v1.0 is released.


* :ref:`genindex`
* :ref:`search`
