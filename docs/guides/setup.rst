==========================================
  Setting up a new project using Pimlico
==========================================

You've decided to use Pimlico to implement a data processing pipeline. So, where do you start?

This guide steps
through the basic setup of your project. You don't have to do everything exactly as suggested here, but it's a
good starting point and follows Pimlico's recommended procedures. It steps through the setup for a very
basic pipeline.

:doc:`A shorter version of this guide <guides/fast_setup>` that zooms through the essential
setup steps is also available.

System-wide configuration
=========================

.. note::

   If you've used Pimlico before, you can skip this step.


Pimlico needs you to specify certain parameters regarding your local system.
Typically this is just
a file in your home directory called ``.pimlico``. :ref:`More details <local-config>`.

It needs to
know where to put output files as it executes. These settings
apply to all Pimlico pipelines you run. Pimlico will
make sure that different pipelines don't interfere
with each other's output (provided you give them different names).

Most of the time, you only need to specify one storage location,
using the ``store`` parameter in your local
config file. (You can specify multiple: :ref:`more details <data-storage>`.)

Create a file ``~/.pimlico`` that looks like this:

.. code-block:: ini

    store=/path/to/storage/directory

All pipelines will use different subdirectories of this one.

Getting started with Pimlico
============================
The procedure for starting a new Pimlico project, using the latest release, is very simple.

Create a new, empty directory to put your project in. Download
`newproject.py <https://raw.githubusercontent.com/markgw/pimlico/master/admin/newproject.py>`_
into the project directory.

Make sure you've got Python installed. Pimlico currently supports Python 2 and 3,
but we strongly recommend using Python 3 unless you have old Python 2 code you
need to run.

Choose a name for your project (e.g. ``myproject``) and run:

.. code-block:: bash

    python newproject.py myproject

This fetches the latest version of Pimlico (now in the ``pimlico/`` subdirectory)
and creates a basic config file, which will define your pipeline.

It also retrieves libraries that Pimlico needs to run. Other libraries
required by specific pipeline modules will be installed as necessary when
you use the modules.

Building the pipeline
=====================
You've now got a config file in ``myproject.conf``. This already includes a
``pipeline`` section, which gives the basic pipeline setup.
It will look something like this:

.. code-block:: ini

    [pipeline]
    name=myproject
    release=<release number>
    python_path=%(project_root)s/src/python

The ``name`` needs to be distinct from any other pipelines that you run –
it's what distinguishes the storage locations.

``release`` is the release of Pimlico that you're using: it's automatically
set to the latest one, which has been downloaded.

If you later try running the same pipeline with an updated version of Pimlico,
it will work fine as long as it's the same minor version (the second part).
The minor-minor third part can be updated and may bring some improvements.
If you use a higher minor version (e.g. 0.10.x when you started with 0.9.24),
there may be backwards incompatible changes, so you'd
need to update your config file, ensuring it plays nicely with the later
Pimlico version.

Getting input
-------------
Now we add our first module to the pipeline. This reads input from a collection of
text files. We use a small subset of the `Europarl corpus <http://www.statmt.org/europarl/>`_
as an example here.
This can be simply adapted to reading the real Europarl corpus or any other corpus
stored in this straightforward way.

`Download and extract the small corpus from
here <https://github.com/markgw/pimlico-data/raw/master/europarl_en_small.tar.gz>`_

In the example below, we have extracted the files to a directory ``data/europarl_demo`` in
the home directory.

.. code-block:: ini

    [input_text]
    type=pimlico.modules.input.text.raw_text_files
    files=%(home)s/data/europarl_demo/*

Doing something: tokenization
-----------------------------
Now, some actual linguistic processing, albeit somewhat uninteresting. Many NLP tools assume that
their input has been divided into sentences and tokenized. To keep things simple, we use a very
basic, regular expression-based tokenizer.

Notice that the output from the previous module feeds into the
input for this one, which we specify simply by naming the module.

.. code-block:: ini

    [tokenize]
    type=pimlico.modules.text.simple_tokenize
    input=input_text

Doing something more interesting: POS tagging
---------------------------------------------
Many NLP tools rely on part-of-speech (POS) tagging. Again, we use OpenNLP, and a standard Pimlico module
wraps the OpenNLP tool.

.. code-block:: ini

    [pos-tag]
    type=pimlico.modules.opennlp.pos
    input=tokenize

Running Pimlico
===============
Now we've got our basic config file ready to go. It's a simple linear pipeline that goes like this:

    read input docs -> group into batches -> tokenize -> POS tag

It's now ready to load and inspect using Pimlico's command-line interface.

Before we can run it, there's one thing missing: the OpenNLP tokenizer module needs access
to the OpenNLP tool. We'll see below how Pimlico sorts that out for you.

Checking everything's dandy
---------------------------
Now you can run the ``status`` command to check that the pipeline can be loaded and see the list of modules.

.. code-block:: bash

    ./pimlico.sh myproject.conf status

To check that specific modules are ready to run, with all software dependencies installed, use the
``run`` command with ``--dry-run`` (or ``--dry``) switch:

.. code-block:: bash

    ./pimlico.sh myproject.conf run tokenize --dry


Fetching dependencies
---------------------
All the standard modules provide easy ways to get hold of their dependencies automatically, or as close as possible.
Most of the time, all you need to do is tell Pimlico to install them.

You use the ``run`` command, with a module name and ``--dry-run``, to check whether a module is ready to run.

.. code-block:: bash

    ./pimlico.sh myproject.conf run tokenize --dry

This will find that things aren't quite ready yet, as the OpenNLP Java
packages are not available. These are not distributed with Pimlico, since they're
only needed if you use an OpenNLP module.

When you run the ``run`` command, Pimlico will offer to install the necessary
software for you. In this case, this involves downloading OpenNLP's jar files
from its web repository to somewhere where the OpenNLP tokenizer module can find it.

Say yes and Pimlico will get everything ready. Simple as that!

There's one more thing to do: the tools we're using
require statistical models. We can simply download the pre-trained English models from the OpenNLP website.

At present, Pimlico doesn't yet provide a built-in way for the modules to
do this, as it does with software libraries,
but it does include a GNU Makefile to make it easy to do:

.. code-block:: bash

    cd ~/myproject/pimlico/models
    make opennlp

Note that the modules we're using default to these standard, pre-trained models, which you're now in a position to 
use. However, if you want to use different models, e.g. for other languages or domains, you can specify them using 
extra options in the module definition in your config file.

If there are any other library problems shown up by the dry run, you'll need to address them
before going any further.


Running the pipeline
====================
What modules to run?
--------------------
Pimlico suggests an order in which to run your modules. In our case, this is pretty obvious, seeing as our
pipeline is entirely linear -- it's clear which ones need to be run before others.

.. code-block:: bash

    ./pimlico.sh myproject.conf status

The output also tells you the current status of each module. At the moment, all the modules are ``UNEXECUTED``.

You might be surprised to see that ``input-text`` features in the list. This is because, although it just
reads the data out of a corpus on disk, there's not quite enough information in the corpus, so we need to run the 
module to collect a little bit of metadata from an initial pass over the corpus. Some input types need this, others
not. In this case, all we're lacking is a count of the total number of documents in the corpus.

.. note::

   To make running your pipeline even simpler, you can abbreviate the command by using a **shebang** in the
   config file. Add a line at the top of ``myproject.conf`` like this:

   .. code-block:: ini

      #!./pimlico.sh

   Then make the conf file executable by running (on Linux):

   .. code-block:: bash

      chmod ug+x myproject.conf

   Now you can run Pimlico for your pipeline by using the config file as an executable command:

   .. code-block:: bash

      ./myproject.conf status

Running the modules
-------------------
The modules can be run using the ``run`` command and specifying the module by name. We do this manually for each module.

.. code-block:: bash

    ./pimlico.sh myproject.conf run input-text
    ./pimlico.sh myproject.conf run tokenize
    ./pimlico.sh myproject.conf run pos-tag

Adding custom modules
=====================
Most likely, for your project you need to do some processing not covered by the built-in Pimlico modules. At this
point, you can start implementing your own modules, which you can distribute along with the config file so that 
people can replicate what you did.

The ``newproject.py`` script has already created a directory where our custom source code will live: ``src/python``,
with some subdirectories according to the standard code layout, with module types and datatypes in separate
packages.

The template pipeline also already has an option ``python_path`` pointing to this directory, so that Pimlico knows where to
find your code. Note that
the code's in a subdirectory of that containing the pipeline config and we specify the custom code path relative to 
the config file, so it's easy to distribute the two together.

Now you can create Python modules or packages in ``src/python``, following the same conventions as the built-in modules
and overriding the standard base classes, as they do. The following articles tell you more about how to do this:

 - :doc:`/guides/module`
 - :doc:`/guides/map_module`
 - :doc:`/core/module_structure`

Your custom modules and datatypes can then simply be used in the
config file as module types.
