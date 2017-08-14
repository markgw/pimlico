==================
  Filter modules
==================

Filter modules appear in pipeline config, but never get executed directly, instead producing their output
on the fly when it is needed.

There are two types of filter modules in Pimlico:

* All :doc:`document map module <map_module>` can be used as filters.
* Other modules may be defined in such a way that they always function as filters.

Document map modules
====================

See :doc:`this guide <map_module>` for how to create document map modules, which process each document in an
input iterable corpus, producing one document in the output corpus for each. Many of the core Pimlico modules
are document map modules.

Any document map module can be used as a filter simply by specifying ``filter=True`` as one of its options in the
config file. It will then not appear in the module execution schedule (output by the ``status`` command), but
will get executed on the fly by any module that uses its output. It will be initialized when the downstream
module starts accessing the output, and then the single-document processing routine will be run on each document
to produce the corresponding output document as the downstream module iterates over the corpus.

It is possible to chain together filter modules in sequence.

Other filter modules
====================

A module can be defined so that it always functions as a filter by setting ``module_executable=False`` on its
module-info class. Pimlico will assume that its outputs are ready as soon as its inputs are ready and will not
include it in the list of modules to be executed. It is up to the module developer then to ensure that the outputs
get produced when necessary.

This form of filter is typically appropriate for very simple transformations of data. For example, a filter might
perform a simple conversion of one datatype into another to allow the output of a module to be used as if it
had a different datatype. However, it is possible to do more sophisticated processing in a filter module, though
the implementation is a little more tricky (:mod:`tar_filter <pimlico.modules.corpora.tar_filter>` is an example
of this).

Define a filter module something like this:

.. code-block:: py

   class ModuleInfo(BaseModuleInfo):
       module_name = "my_module_name"
       module_executable = False  # This is the crucial instruction to treat this as a filter
       module_inputs = []         # Define inputs
       module_outputs = []        # Define at least one output, which we'll produce as needed
       module_options = {}        # Any options you need

       def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
           # Here we produce the desired output datatype, using the inputs acquired from self.get_input(name)
           return MyOutputDatatype()


