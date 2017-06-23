===================
Module dependencies
===================

In a Pimlico pipeline, you typically use lots of different external software packages. Some are Python packages,
others system tools, Java libraries, whatever. Even the core modules that core with Pimlico between them
depend on a huge amount of software.

Naturally, we don't want to have to install *all* of this software before you can run even a simple Pimlico
pipeline that doesn't use all (or any) of it. So, we keep the core dependencies of Pimlico to an absolute
minimum, and then check whether the necessary software dependencies are installed each time a pipeline module
is going to be run.

Core dependencies
=================
Certain dependencies are required for Pimlico to run at all, or needed so often that you wouldn't get far without
installing them. These are defined in :mod:`pimlico.core.dependencies.core`, and when you run the Pimlico command-line
interface, it checks they're available and tries to install them if they're not.

Module dependencies
===================
Each module type defines its own set of software dependencies, if it has any. When you try to run the module,
Pimlico runs some checks to try to make sure that all of these are available.

If some of them are not, it may be possible to install them automatically, straight from Pimlico. In particular,
many Python packages can be very easily installed using `Pip <https://pypi.python.org/pypi/pip>`_. If this is
the case for one of the missing dependencies, Pimlico will tell you in the error output, and you can install
them using the ``install`` command (with the module name/number as an argument).

.. _virtualenv-for-deps:

Virtualenv
==========
In order to simplify automatic installation, Pimlico is always run within a virtual environment, using
`Virtualenv <https://virtualenv.pypa.io/en/stable/>`_. This means that any Python packages installed by Pip will
live in a local directory within the Pimlico codebase that you're running and won't interfere with anything else
on your system.

When you run Pimlico for the first time, it will create a new virtualenv for this purpose. Every time you run it
after that, it will use this same environment, so anything you install will continue to be available.

Custom virtualenv
-----------------
Most of the time, you don't even need to be aware of the virtualenv that Python's running in [#env_loc]_.
Under certain circumstances, you might need to use a custom virtualenv.

For example, say
you're running your pipeline over different servers, but have the pipeline and Pimlico codebase on a shared
network drive. Then you can find that the software installed in the virtualenv on one machine is incompatible
with the system-wide software on the other.

The following procedure sets up an alternative virtualenv, which you can use on your second
machine.

Open a terminal and ``cd`` into your project directory (Pimlico should be in the ``pimlico`` subdirectory).

.. code:: sh

   $ python pimlico/lib/libutils/create_virtualenv.py pimlico/lib/myenv

Replace ``myenv`` with a name that better reflects its use (e.g. name of the server).

Every time you run Pimlico on that server, set the ``VIRTUALENV`` environment variable to
point to the virtualenv directory that you just created. For example:

.. code:: sh

   $ VIRTUALENV=pimlico/lib/myenv ./pimlico.sh mypipeline.conf status

Defining module dependencies
============================

.. todo::

   Describe how module dependencies are defined for different types of deps

Some examples
=============

.. todo::

   Include some examples from the core modules of how deps are defined and some special cases of software fetching



.. rubric:: Footnotes

.. [#env_loc] If you're interested, it lives in ``pimlico/lib/python_env``
