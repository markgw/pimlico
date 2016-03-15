from pimlico.core.modules.base import BaseModuleInfo, BaseModuleExecutor
from pimlico.datatypes.tar import TarredCorpus, AlignedTarredCorpora, TarredCorpusWriter


class DocumentMapModuleInfo(BaseModuleInfo):
    """
    Abstract module type that maps each document in turn in a corpus. It produces a single output
    document for every input.

    Subclasses should specify the input types, which should all be subclasses of
    TarredCorpus, and output types, the first of which (i.e. default) should also be a
    subclass of TarredCorpus. The base class deals with iterating over the input(s) and
    writing the outputs to a new TarredCorpus. The subclass only needs to implement the
    mapping function applied to each document (in its executor).

    """
    # Most subclasses will want to override this to give a more specific datatype for the output
    module_outputs = [("documents", TarredCorpus)]


class DocumentMapModuleExecutor(BaseModuleExecutor):
    """
    Base class for executors for document map modules. Subclasses should provide the behaviour
    for each individual document.

    """
    def process_document(self, filename, *docs):
        raise NotImplementedError

    def preprocess(self):
        """
        Allows subclasses to define a set-up procedure to be called before corpus processing begins.
        """
        pass

    def postprocess(self):
        """
        Allows subclasses to define a finishing procedure to be called after corpus processing if finished.
        """
        pass

    def execute(self, module_instance_info):
        # We may have multiple inputs, which should be aligned tarred corpora
        # If there's only one, this also works
        input_iterator = AlignedTarredCorpora(module_instance_info.inputs)

        # Call the set-up routine, if one's been defined
        self.preprocess()

        # Prepare a corpus writer for the output
        with TarredCorpusWriter(module_instance_info.get_output_dir()) as writer:
            for archive, filename, docs in input_iterator.archive_iter():
                # Get the subclass to process the doc
                result = self.process_document(filename, *docs)
                # Write the result to the output corpus
                writer.add_document(archive, filename, result)

        # Call the finishing-off routine, if one's been defined
        self.postprocess()
