==========================================
  Setting up a new project using Pimlico
==========================================

You've decided to use Pimlico to implement a data processing pipeline. So, where do you start?

This guide steps
through the basic setup of your project. You don't have to do everything exactly as suggested here, but it's a
good starting point and follows Pimlico's recommended procedures. It steps through the setup for a very
basic pipeline.

System-wide configuration
=========================
Pimlico needs you to specify certain parameters regarding your local system.

It needs to
know where to put output files as it executes. Settings are given in a config file in your home directory and
apply to all Pimlico pipelines you run. Note that Pimlico will make sure that different pipelines don't interfere 
with each other's output (provided you give them different names).

There are two locations you need to specify: **short-term** and **long-term storage**.

The **short-term store** should be on a disk that's as fast as possible to write to. For example, avoid using an NFS
disk. It needs to be large enough to store output between pipeline stages, though you can easily move
output from earlier stages into the long-term store as you go along.

The **long-term store** is where things are typically put at the end of
a pipeline. It therefore doesn't need to be super-fast to access, but you may want it to be in a location that gets 
backed up, so you don't lose your valuable output.

For a simple setup, these could be just two subdirectories of the same directory. However, it can be
useful to distinguish them.

Create a file `~/.pimlico` that looks like this:

.. code-block:: ini

    long_term_store=/path/to/long-term/store
    short_term_store=/path/to/short-term/store

Remember, these paths are not specific to a pipeline: all pipelines will use different subdirectories of these ones.

Getting started with Pimlico
============================
The procedure for starting a new Pimlico project, using the latest release, is very simple.

Create a new, empty directory to put your project in. Download
`newproject.py <https://gitlab.com/markgw/pimlico/raw/master/admin/newproject.py>`_ into the project directory.

Choose a name for your project (e.g. `myproject`) and run:

.. code-block:: bash

    python newproject.py myproject

This fetches the latest version of Pimlico (now in the `pimlico/` directory) and creates a basic config file template,
which will define your pipeline.

It also retrieves some libraries that Pimlico needs to run. Other libraries required by specific pipeline modules will
be installed as necessary when you use the modules.

Building the pipeline
=====================
You've now got a config file in `myproject.conf`. This already includes a `pipeline` section, which gives the
basic pipeline setup. It will look something like this:

.. code-block:: ini

    [pipeline]
    name=myproject
    release=<release number>
    python_path=%(project_root)s/src/python

The `name` needs to be distinct from any other pipelines that you run &ndash; it's what distinguishes the storage 
locations.

`release` is the release of Pimlico that you're using: it's automatically set to the latest one, which has
been downloaded.

If you later 
try running the same pipeline with an updated version of Pimlico, it will work fine as long as it's the same major 
version (the first digit). Otherwise, there may be backwards incompatible changes, so you'd
need to update your config file, ensuring it plays nicely with the later Pimlico version.

Getting input
-------------
Now we add our first module to the pipeline. This reads input from XML files and iterates of `<doc>` tags to get 
documents. This is how the Gigaword corpus is stored, so if you have Gigaword, just set the path to point to it.

.. todo::

   Use a dataset that everyone can get to in the example

.. code-block:: ini

    [input-text]
    type=pimlico.datatypes.XmlDocumentIterator
    path=/path/to/data/dir

Perhaps your corpus is very large and you'd rather try out your pipeline on a small subset. In that case, add the 
following option:

.. code-block:: ini

    truncate=1000

.. note::
   For a neat way to define a small test version of your pipeline and keep its output separate from the main
   pipeline, see :doc:`/core/variants`.

Grouping files
--------------
The standard approach to storing data between modules in Pimlico is to group them together into batches of documents, 
storing each batch in a tar archive, containing a file for every document. This works nicely with large corpora,
where having every document as a separate file would cause filesystem difficulties and having all documents in the 
same file would result in a frustratingly large file.

We can do the grouping on the fly as we read data from the input corpus. The `tar_filter` module groups
documents together and subsequent modules will all use the same grouping to store their output, making it easy to 
align the datasets they produce.

.. code-block:: ini

    [tar-grouper]
    type=pimlico.modules.corpora.tar_filter
    input=input-text

Doing something: tokenization
-----------------------------
Now, some actual linguistic processing, albeit somewhat uninteresting. Many NLP tools assume that
their input has been divided into sentences and tokenized. The OpenNLP-based tokenization module does both of these 
things at once, calling OpenNLP tools.

Notice that the output from the previous module feeds into the input for this one, which we specify simply by naming 
the module.

.. code-block:: ini

    [tokenize]
    type=pimlico.modules.opennlp.tokenize
    input=tar-grouper

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

Before we can run it, there's one thing missing: three of these modules have their own dependencies, so we need
to get hold of the libraries they use. The input reader uses the Beautiful Soup python library and the tokenization 
and POS tagging modules use OpenNLP.

Fetching dependencies
---------------------
All the standard modules provide easy ways to get hold of their dependencies automatically, or as close as possible.
Most of the time, all you need to do is tell Pimlico to install them.

You can use the `check` command, with a module name, to check whether a module is ready to run.

.. code-block:: bash

    ./pimlico.sh myproject.conf check tokenize

In this case, it will tell you that some libraries are missing, but they can be installed automatically. Simply issue
the `install` command for the module.

.. code-block:: bash

    ./pimlico.sh myproject.conf install tokenize

Simple as that.

There's one more thing to do: the tools we're using
require statistical models. We can simply download the pre-trained English models from the OpenNLP website.

At present, Pimlico doesn't yet provide a built-in way for the modules to do this, as it does with software libraries,
but it does include a GNU Makefile to make it easy to do:

.. code-block:: bash

    cd ~/myproject/pimlico/models
    make opennlp

Note that the modules we're using default to these standard, pre-trained models, which you're now in a position to 
use. However, if you want to use different models, e.g. for other languages or domains, you can specify them using 
extra options in the module definition in your config file.

Checking everything's dandy
---------------------------
Now you can run the `check` command to check that the modules are ready to run. To check the whole pipeline's
dependencies, run:

.. code-block:: bash

    ./pimlico.sh myproject.conf check all

With any luck, all the checks will be successful. If not, you'll need to address any problems with dependencies
before going any further.

Running the pipeline
====================
What modules to run?
--------------------
Pimlico can now suggest an order in which to run your modules. In our case, this is pretty obvious, seeing as our 
pipeline is entirely linear &ndash; it's clear which ones need to be run before others.

.. code-block:: bash

    ./pimlico.sh myproject.conf status

The output also tells you the current status of each module. At the moment, all the modules are `UNEXECUTED`.

You'll notice that the `tar-grouper` module doesn't feature in the list. This is because it's a filter &ndash; 
it's run on the fly while reading output from the previous module (i.e. the input), so doesn't have anything to 
run itself.

You might be surprised to see that `input-text` *does* feature in the list. This is because, although it just
reads the data out of a corpus on disk, there's not quite enough information in the corpus, so we need to run the 
module to collect a little bit of metadata from an initial pass over the corpus. Some input types need this, others
not. In this case, all we're lacking is a count of the total number of documents in the corpus.

Running the modules
-------------------
The modules can be run using the `run` command and specifying the module by name. We do this manually for each module. 

.. code-block:: bash

    ./pimlico.sh myproject.conf run input-text
    ./pimlico.sh myproject.conf run tokenize
    ./pimlico.sh myproject.conf run pos-tag

Adding custom modules
=====================
Most likely, for your project you need to do some processing not covered by the built-in Pimlico modules. At this
point, you can start implementing your own modules, which you can distribute along with the config file so that 
people can replicate what you did.

The `newproject.py` script has already created a directory where our custom source code will live: `src/python`,
with some subdirectories according to the standard code layout, with module types and datatypes in separate
packages.

The template pipeline also already has an option `python_path` pointing to this directory, so that Pimlico knows where to
find your code. Note that
the code's in a subdirectory of that containing the pipeline config and we specify the custom code path relative to 
the config file, so it's easy to distribute the two together.

Now you can create Python modules or packages in `src/python`, following the same conventions as the built-in modules
and overriding the standard base classes, as they do. The following articles tell you more about how to do this:

 - :doc:`/guides/module`
 - :doc:`/guides/map_module`
 - :doc:`/core/module_structure`

Your custom modules and datatypes can then simply be used in the
config file as module types.
