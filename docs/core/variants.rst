=================
Pipeline variants
=================

You can create several different versions of a pipeline, called pipeline *variants*
in a single config file. The data corresponding to each will be kept completely
separate.
This is useful when you want multiple versions of a pipeline that are almost
identical, but have some small differences.

The most common use of this, though by no means the only,
is to create a variant that is faster to run than
the main pipeline for the purposes of quickly testing the whole pipeline during
development.

Every pipeline has by default one variant, called ``main``. You define other variants
simply by using special directives to mark particular lines as belonging to a particular
variant. Lines with no variant marking will appear in all variants.

Loading variants
----------------

If you don't specify otherwise when loading a pipeline, the ``main`` variant will be
loaded. Use the ``--variant`` parameter (or ``-v``) to specify another variant by
name:

.. code-block:: sh

   ./pimlico.sh mypipeline.conf -v smaller status

To see a list of all available variants of a particular pipeline, use the
:ref:`command_variants` command:

.. code-block:: sh

   ./pimlico.sh mypipeline.conf variants

Variant directives
------------------

Directives are processed when a pipeline config file is read in, before the file is
parsed to build a pipeline. They are lines that begin with ``%%``, followed
by the directive name and any arguments. See :ref:`config-directives` for details
of other directives.

- ``variant``:
   This line will be included only when loading a particular variant of a pipeline.

   The variant name is
   specified in the form: ``variant:variant_name``. You may include the line in more
   than one variant by specifying multiple names, separated by commas (and no spaces). You can use the default
   variant "main", so that the line will be left out of other variants. The rest of the line, after the directive
   and variant name(s) is the content that will be included in those variants.

   .. code-block:: ini
      :emphasize-lines: 3,4

      [my_module]
      type=path.to.module
      %%variant:main size=52
      %%variant:smaller size=7

   An alternative notation makes config files more readable. Instead of
   ``%%variant:variant_name``, write ``%%(variant_name)``. So the above example becomes:

   .. code-block:: ini
      :emphasize-lines: 3,4

         [my_module]
         type=path.to.module
         %%(main) size=52
         %%(smaller) size=7

- ``novariant``:
   A line to be included only when not loading a variant of the pipeline. Equivalent to ``variant:main``.

   .. code-block:: ini
      :emphasize-lines: 3

      [my_module]
      type=path.to.module
      %%novariant size=52
      %%variant:smaller size=7

Example
-------

The following example config file, defines one variant, ``small``, aside from the default
``main`` variant.

.. code-block:: ini
   :emphasize-lines: 3

   [pipeline]
   name=myvariants
   release=0.8
   python_path=%(project_root)s/src/python

   # Load a dataset
   [input_data]
   type=pimlico.modules.input.text.raw_text_files
   files=%(home)s/data/*

   # For the small version, we cut down the dataset to just 10 documents
   # We don't need this module at all in the main variant
   %%(small) [small_data]
   %%(small) type=pimlico.modules.corpora.subset
   %%(small) size=10

   # Tokenize the text
   # Control where the input data comes from in the different variants
   # The main variant simply uses the full, uncut corpus
   [tokenize]
   type=pimlico.modules.text.simple_tokenize
   %%(small) input=small_data
   %%(main) input=input_data

The main variant will be loaded if you don't specify otherwise. In this version the module
``small_data`` doesn't exist at all and ``tokenize`` takes its input from ``input_data``.

.. code-block:: sh

   ./pimlico.sh myvariants.conf status

You can load the small variant by giving its name on the command line. This includes the
``small_data`` module and ``tokenize`` gets its input from there, making it much faster
to test.

.. code-block:: sh

   ./pimlico.sh myvariants.conf -v small status
