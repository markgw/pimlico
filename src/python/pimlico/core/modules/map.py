from traceback import format_exc

from pimlico.core.modules.base import BaseModuleInfo, BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError, StopProcessing
from pimlico.datatypes.base import InvalidDocument
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
    def process_document(self, archive, filename, *docs):
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
        invalid_inputs = 0
        invalid_outputs = 0
        try:
            # Prepare a corpus writer for the output
            with multiwith(*self.get_writers()) as writers:
                for archive, filename, docs in pbar(input_iterator.archive_iter()):
                    # Useful to know in output
                    if any(type(d) is InvalidDocument for d in docs):
                        invalid_inputs += 1

                    # Get the subclass to process the doc
                    results = self.process_document(archive, filename, *docs)

                    if type(results) is InvalidDocument:
                        # Just got a single invalid document out: write it out to every output
                        results = [results] * len(writers)
                    elif type(results) is not tuple:
                        # If the processor only produces a single result and there's only one output, that's fine
                        results = (results,)
                    if len(results) != len(writers):
                        raise ModuleExecutionError(
                            "%s executor's process_document() returned %d results for a document, but the module has "
                            "%d outputs" % (
                                type(self).__name__, len(results), len(writers)
                            )
                        )

                    # Just for the record (useful output)
                    if any(type(r) is InvalidDocument for r in results):
                        invalid_outputs += 1

                    # Write the result to the output corpora
                    for result, writer in zip(results, writers):
                        writer.add_document(archive, filename, result)

            complete = True
            self.log.info("Input contained %d invalid documents, output contained %d" %
                          (invalid_inputs, invalid_outputs))
        finally:
            # Call the finishing-off routine, if one's been defined
            if complete:
                self.log.info("Document mapping complete. Finishing off")
            else:
                self.log.info("Document mapping failed. Finishing off")
            self.postprocess(error=not complete)


def skip_invalid(fn):
    """
    Decorator to apply to process_document() methods where you want to skip doing any processing if any of the
    input documents are invalid and just pass through the error information.

    """
    def _fn(self, archive, filename, *docs):
        invalid = [doc for doc in docs if type(doc) is InvalidDocument]
        if len(invalid):
            # If there's more than one InvalidDocument among the inputs, just return the first one
            return invalid[0]
        else:
            return fn(self, archive, filename, *docs)
    return _fn


def invalid_doc_on_error(fn):
    """
    Decorator to apply to process_document() methods that causes all exceptions to be caught and an InvalidDocument
    to be returned as the result, instead of letting the error propagate up and call a halt to the whole corpus
    processing.

    """
    def _fn(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except StopProcessing:
            # Processing was cancelled, killed or otherwise called to a halt
            # Don't report this as an error processing a doc, but raise it
            raise
        except Exception, e:
            # Error while processing the document: output an invalid document, with some error information
            return InvalidDocument(self.info.module_name,  "%s\n%s" % (e, format_exc()))
    return _fn
