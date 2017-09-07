==============================
  My Project's Documentation
==============================

Project intro here.

You can use ``make modules`` to automatically generate module documentation for your
custom Pimlico modules. By default, it will appear in the ``modules`` subdirectory
and then you can use something like what's below to include its index in the TOC.

Likewise, you can use Sphinx's apidoc to generate API docs for non-module code,
if you have any.

Contents
========

.. toctree::
   :maxdepth: 1
   :titlesonly:

   Pimlico modules <modules/packagename.modules>
   API docs <api/packagename>


* :ref:`genindex`
* :ref:`search`
