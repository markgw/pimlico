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

    def get_writer(self, output_name, output_dir, append=False):
        """
        Get the writer instance that will be given processed documents to write. Should return
        a subclass of TarredCorpusWriter. The default implementation instantiates a plain
        TarredCorpusWriter.

        """
        return TarredCorpusWriter(output_dir, append=append)

    def get_writers(self, append=False):
        return tuple(self.get_writer(name, self.get_absolute_output_dir(name), append=append)
                     for name in self.output_names)

    def get_detailed_status(self):
        status_lines = super(DocumentMapModuleInfo, self).get_detailed_status()
        if self.status == "PARTIALLY_PROCESSED":
            status_lines.append("Processed %d documents" % self.get_metadata()["docs_completed"])
            status_lines.append("Last doc completed: %s" % self.get_metadata()["last_doc_completed"])
        return status_lines


class DocumentMapModuleExecutor(BaseModuleExecutor):
    """
    Base class for executors for document map modules. Subclasses should provide the behaviour
    for each individual document.

    """
    def __init__(self, module_instance_info):
        super(DocumentMapModuleExecutor, self).__init__(module_instance_info)

        # We may have multiple inputs, which should be aligned tarred corpora
        # If there's only one, this also works
        self.input_corpora = [self.info.get_input(input_name)
                              for input_name in self.info.input_names]
        self.input_iterator = AlignedTarredCorpora(self.input_corpora)

    def process_document(self, archive, filename, *docs):
        raise NotImplementedError

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

    def retrieve_processing_status(self):
        # Check the metadata to see whether we've already partially completed this
        if self.info.status == "PARTIALLY_PROCESSED":
            docs_completed = self.info.get_metadata()["docs_completed"]
            first_archive, __, first_filename = self.info.get_metadata()["last_doc_completed"].partition("/")
            start_after = (first_archive, first_filename)
            self.log.info(
                "Module has been partially executed already; picking up where we left off, after doc %s/%s "
                "(skipping %d docs, %d to process)" %
                (start_after[0], start_after[1], docs_completed, (len(self.input_iterator) - docs_completed))
            )
        else:
            docs_completed = 0
            start_after = None
        return docs_completed, start_after

    def update_processing_status(self, docs_completed, archive_name, filename):
        self.info.set_metadata_values({
            "status": "PARTIALLY_PROCESSED",
            "last_doc_completed": "%s/%s" % (archive_name, filename),
            "docs_completed": docs_completed,
        })

    def execute(self):
        # Call the set-up routine, if one's been defined
        self.log.info("Preparing document map execution")
        self.preprocess()

        complete = False
        invalid_inputs = 0
        invalid_outputs = 0

        docs_completed_now = 0
        docs_completed_before, start_after = self.retrieve_processing_status()

        pbar = get_progress_bar(len(self.input_iterator) - docs_completed_before,
                                title="%s map" % self.info.module_type_name.replace("_", " ").capitalize())

        try:
            # Prepare a corpus writer for the output
            with multiwith(*self.info.get_writers(append=start_after is not None)) as writers:
                for archive, filename, docs in pbar(self.input_iterator.archive_iter(start_after=start_after)):
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

                    # Update the module's metadata to say that we've completed this document
                    docs_completed_now += 1
                    self.update_processing_status(docs_completed_before+docs_completed_now, archive, filename)
            complete = True
            self.log.info("Input contained %d invalid documents, output contained %d" %
                          (invalid_inputs, invalid_outputs))
        finally:
            # Call the finishing-off routine, if one's been defined
            if complete:
                self.log.info("Document mapping complete. Finishing off")
            else:
                self.log.info("Document mapping failed")
            self.postprocess(error=not complete)

            if not complete and self.info.status == "PARTIALLY_PROCESSED":
                self.log.info("Processed documents recorded: restart processing where you left off by calling run "
                              "again once you've fixed the problem (%d docs processed in this run, %d processed in "
                              "total)" % (docs_completed_now, docs_completed_before+docs_completed_now))


def skip_invalid(fn):
    """
    Decorator to apply to document map executor process_document() methods where you want to skip doing any
    processing if any of the input documents are invalid and just pass through the error information.

    Be careful not to confuse this with the process_document() methods on datatypes. You don't need a decorator
    on them to skip invalid documents, as it's not called on them anyway.

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
            if isinstance(self, TarredCorpus):
                # Decorator wrapped a process_document() method on a datatype
                # Instead of the module name, output the datatype name and its base dir
                return InvalidDocument("datatype:%s[%s]" % (self.datatype_name, self.base_dir),
                                       "%s\n%s" % (e, format_exc()))
            else:
                return InvalidDocument(self.info.module_name,  "%s\n%s" % (e, format_exc()))
    return _fn
