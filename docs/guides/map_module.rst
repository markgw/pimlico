================================
  Writing document map modules
================================

.. todo::

   Write a guide to building document map modules


Skeleton new module
===================
To make developing a new module a little quicker, here's a skeleton module info and executor for a document map
module. It follows the most common method for defining the executor, which is to use the multiprocessing-based
executor factory.

.. code-block:: py

    from pimlico.core.modules.map import DocumentMapModuleInfo
    from pimlico.datatypes.tar import TarredCorpusType

    class ModuleInfo(DocumentMapModuleInfo):
        module_type_name = "NAME"
        module_readable_name = "READABLE NAME"
        module_inputs = [("NAME", TarredCorpusType(DOCUMENT_TYPE))]
        module_outputs = [("NAME", PRODUCED_TYPE)]
        module_options = {
            "OPTION_NAME": {
                "help": "DESCRIPTION",
                "type": TYPE,
                "default": VALUE,
            },
        }

        def get_software_dependencies(self):
            return super(ModuleInfo, self).get_software_dependencies() + [
                # Add your own dependencies to this list
            ]

        def get_writer(self, output_name, output_dir, append=False):
            if output_name == "NAME":
                # Instantiate a writer for this output, using the given output dir
                # and passing append in as a kwarg
                return WRITER_CLASS(output_dir, append=append)


A bare-bones executor:

.. code-block:: py

    from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


    def process_document(worker, archive_name, doc_name, *data):
        # Do something to process the document...

        # Return an object to send to the writer
        return output


    ModuleExecutor = multiprocessing_executor_factory(process_document)


Or getting slightly more sophisticated:

.. code-block:: py

    from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


    def process_document(worker, archive_name, doc_name, *data):
        # Do something to process the document

        # Return a tuple of objects to send to each writer
        # If you only defined a single output, you can just return a single object
        return output1, output2, ...


    # You don't have to, but you can also define pre- and postprocessing
    # both at the executor level and worker level

    def preprocess(executor):
        pass


    def postprocess(executor, error=None):
        pass


    def set_up_worker(worker):
        pass


    def tear_down_worker(worker, error=None):
        pass


    ModuleExecutor = multiprocessing_executor_factory(
        process_document,
        preprocess_fn=preprocess, postprocess_fn=postprocess,
        worker_set_up_fn=set_up_worker, worker_tear_down_fn=tear_down_worker,
    )
