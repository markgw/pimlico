from pimlico.core.modules.base import BaseModuleInfo, BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.datatypes.tar import TarredCorpus, AlignedTarredCorpora, TarredCorpusWriter
from pimlico.utils.core import multiwith
from pimlico.utils.progress import get_progress_bar


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

    def get_writer(self, output_name):
        """
        Get the writer instance that will be given processed documents to write. Should return
        a subclass of TarredCorpusWriter. The default implementation instantiates a plain
        TarredCorpusWriter.

        """
        return TarredCorpusWriter(self.info.get_output_dir(output_name))

    def get_writers(self):
        return tuple(self.get_writer(name) for name in self.info.output_names)

    def preprocess(self):
        """
        Allows subclasses to define a set-up procedure to be called before corpus processing begins.
        """
        pass

    def postprocess(self, error=False):
        """
        Allows subclasses to define a finishing procedure to be called after corpus processing if finished.
        """
        pass

    def execute(self):
        # We may have multiple inputs, which should be aligned tarred corpora
        # If there's only one, this also works
        self.input_corpora = [self.info.get_input(input_name)
                              for input_name in self.info.input_names]
        input_iterator = AlignedTarredCorpora(self.input_corpora)

        # Call the set-up routine, if one's been defined
        self.log.info("Preparing document map execution for %s documents" % len(input_iterator))
        self.preprocess()

        pbar = get_progress_bar(len(input_iterator),
                                title="%s map" % self.info.module_type_name.replace("_", " ").capitalize())
        complete = False
        try:
            # Prepare a corpus writer for the output
            with multiwith(*self.get_writers()) as writers:
                for archive, filename, docs in pbar(input_iterator.archive_iter()):
                    # Get the subclass to process the doc
                    results = self.process_document(archive, filename, *docs)

                    # If the processor only produces a single result and there's only one output, that's fine
                    if type(results) is not tuple:
                        results = (results,)
                    if len(results) != len(writers):
                        raise ModuleExecutionError(
                            "%s executor's process_document() returned %d results for a document, but the module has "
                            "%d outputs" % (
                                type(self).__name__, len(results), len(writers)
                            )
                        )

                    # Write the result to the output corpora
                    for result, writer in zip(results, writers):
                        writer.add_document(archive, filename, result)

            complete = True
        finally:
            # Call the finishing-off routine, if one's been defined
            if complete:
                self.log.info("Document mapping complete. Finishing off")
            else:
                self.log.info("Document mapping failed. Finishing off")
            self.postprocess()
