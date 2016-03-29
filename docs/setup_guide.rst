==========================================
  Setting up a new project using Pimlico
==========================================

*Pimlico v0.1*

You've decided to use Pimlico to implement a data processing pipeline. So, where do you start?

This guide steps
through the basic setup of your project. You don't have to do everything exactly as suggested here, but it's a
good starting point and follows Pimlico's recommended procedures. It steps through the setup for a very
basic pipeline.

Getting Pimlico
===============
You'll want to use the latest release of Pimlico. Check the website and download the codebase as a tarball.

Create a new directory to put your project in and extract the codebase into
a directory `pimlico` within the project directory. Let's say we're using `~/myproject/`.

.. code-block:: bash
    mkdir ~/myproject
    cd ~/myproject
    mv /path/to/downloaded/tarball.tar.gz .
    tar -zxf tarball.tar.gz
    rm tarball.tar.gz

Depending on what you want to do with Pimlico, you'll
also need to fetch dependencies. Let's start by getting the basic dependencies that will be needed regardless of what
module types you use.

.. code-block:: bash
    cd pimlico/lib/python
    make core

System-wide configuration
=========================
Pimlico needs you to specify certain parameters regarding your local system. It needs to
know where to put output files as it executes. Settings are given in a config file in your home directory and
apply to all Pimlico pipelines you run. Note that Pimlico will make sure that different pipelines don't interfere 
with each other's output (provided you give them different names).

There are two locations you need to specify: **short-term** and **long-term storage**.
These could be just two subdirectories of the same directory. However, it can be
useful to distinguish them.

The **short-term store** should be on a local disk (not NFS) that's as fast as possible to
write to. It needs to be large enough to store output between pipeline stages (though if necessary you could delete
output from earlier stages as you go along).

The **long-term store** is where things are typically put at the end of
a pipeline. It therefore doesn't need to be super-fast to access, but you may want it to be in a location that gets 
backed up, so you don't lose your valuable output.

Create a file `~/.pimlico` that looks like this:

.. code-block:: ini
    long_term_store=/path/to/long-term/store
    short_term_store=/path/to/short-term/store

Remember, these paths are not specific to a pipeline: all pipelines will use different subdirectories of these ones.

Creating a config file
======================
In the simplest case, the only thing left to do is to write a **config file** for your pipeline and run it! Let's make
a simple one as an example.

We're going to create the file `~/myproject/pipeline.conf`. Start by writing a `pipeline` section to give the
basic pipeline setup.

.. code-block:: ini
    [pipeline]
    name=myproject
    release=0.1

The `name` needs to be distinct from any other pipelines that you run &ndash; it's what distinguishes the storage 
locations.

`release` is the release of Pimlico that you're using: set it to the one you downloaded.

If you later 
try running the same pipeline with an updated version of Pimlico, it will work fine as long as it's the same major 
version (the first digit). Otherwise, there are likely to be backwards incompatible changes in the library, so you'd 
need to either get an older version of Pimlico, or update your config file, ensuring it plays nicely with the later 
Pimlico version.

Getting input
-------------
Now we add our first module to the pipeline. This reads input from XML files and iterates of `<doc>` tags to get 
documents. This is how the Gigaword corpus is stored, so if you have Gigaword, just set the path to point to it.

**TODO: add an example that everyone can run** 

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
   pipeline, see :doc:`variants`.

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
All the standard modules provide easy ways to get hold of their dependencies via makefiles for GNU Make. Let's get 
Beautiful Soup.

.. code-block:: bash
    cd ~/myproject/pimlico/lib/python
    make bs4

Simple as that.

OpenNLP is a little trickier. To make things simple, we just get all the OpenNLP tools and libraries required to
run the OpenNLP wrappers at once. The `opennlp` make target gets all of these at once.

.. code-block:: bash
    cd ~/myproject/pimlico/lib/java
    make opennlp

At the moment, it's also necessary to build the Java wrappers around OpenNLP that are provided as part of Pimlico. For 
this, you'll need a Java compiler installed on your system.

.. code-block:: bash
    cd ~/myproject/pimlico
    ant opennlp

.. note::
   In later versions of Pimlico, this Java building won't be necessary. I just haven't got round to bundling the
   compiled wrapper library yet.

There's one more thing to do: the tools we're using
require statistical models. We can simply download the pre-trained English models from the OpenNLP website.

.. code-block:: bash
    cd ~/myproject/pimlico/models
    make opennlp

Note that the modules we're using default to these standard, pre-trained models, which you're now in a position to 
use. However, if you want to use different models, e.g. for other languages or domains, you can specify them using 
extra options in the module definition in your config file.

Checking everything's dandy
---------------------------
We now run some checks over the pipeline to make sure that our config file is valid and we've got Pimlico basically 
ready to run.

.. code-block:: bash
    cd ~/myproject/
    ./pimlico/bin/pimlico pipeline.conf check

With any luck, all the checks will be successful. If not, you'll need to address any problems with dependencies 
before going any further.

So far, we've checked the basic Pimlico dependencies and the config file's validity, but not the dependencies of 
each module. This is intentional: in some setups, we might run different modules on different machines or environments, 
such that in no one of them do all modules have all of their dependencies. For us, however, this isn't the case, so 
we can run further checks on the *runtime* dependencies of all our modules.

.. code-block:: bash
    ./pimlico/bin/pimlico pipeline.conf check --runtime

If that works as well, we're able to start running modules.

Running the pipeline
====================
What modules to run?
--------------------
Pimlico can now suggest an order in which to run your modules. In our case, this is pretty obvious, seeing as our 
pipeline is entirely linear &ndash; it's clear which ones need to be run before others.

.. code-block:: bash
    ./pimlico/bin/pimlico pipeline.conf schedule

The output also tells you the current status of each module. At the moment, all the modules are `UNSTARTED`.

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
    ./pimlico/bin/pimlico.sh pipeline.conf run input-text
    ./pimlico/bin/pimlico.sh pipeline.conf run tokenize
    ./pimlico/bin/pimlico.sh pipeline.conf run pos-tag

Adding custom modules
=====================
Most likely, for your project you need to do some processing not covered by the built-in Pimlico modules. At this
point, you can start implementing your own modules, which you can distribute along with the config file so that 
people can replicate what you did.

First, let's create a directory where our custom source code will live.

.. code-block:: bash
    cd ~/myproject
    mkdir -p src/python

Now we need Pimlico to find the code we put in there. We simply add an option to our pipeline configuration. Note that 
the code's in a subdirectory of that containing the pipeline config and we specify the custom code path relative to 
the config file, so it's easy to distribute the two together.

Add this option to the `[pipeline]` section in the config file:

.. code-block:: ini
    python_path=src/python

Now you can create Python modules or packages in `src/python`, following the same conventions as the built-in modules 
(see `pimlico/src/python/pimlico/modules/`) and overriding the standard base classes, as they do. (Details of how to 
do this are outside the scope of this tutorial.)

Your custom modules and datatypes can then simply be used in the
config file as module types.
