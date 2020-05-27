from importlib import reload

import pkg_resources
import spacy
from spacy import about
from spacy.cli.download import get_json, get_compatibility, get_version, download_model

from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.singleproc import single_process_executor_factory


def preprocess(executor):
    model = executor.info.options["model"]

    try:
        nlp = spacy.load(model)
    except IOError:
        # Couldn't load spacy model
        if not executor.info.options["on_disk"]:
            # If not loading from disk, we need to run the spacy download command
            executor.log.info("Downloading the model '{}'".format(model))
            if not download(model):
                raise ModuleExecutionError("Model could not be downloaded")
        else:
            raise
        # Now the model should be available
        nlp = spacy.load(model)

    executor.tokenizer = nlp.Defaults.create_tokenizer(nlp)
    executor.sentencizer = nlp.create_pipe("sentencizer")


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Apply tokenization to the raw text
    doc = worker.executor.tokenizer(doc.text)
    # Apply sentence segmentation to the doc
    doc = worker.executor.sentencizer(doc)

    # Now doc.sents contains the separated sentences
    return {"sentences": [[token.text for token in sent] for sent in doc.sents]}


ModuleExecutor = single_process_executor_factory(process_document, preprocess_fn=preprocess)


def download(model):
    """
    Replicates what spaCy does in its cmdline interface.

    """
    dl_tpl = "{m}-{v}/{m}-{v}.tar.gz#egg={m}=={v}"
    shortcuts = get_json(about.__shortcuts__, "available shortcuts")
    model_name = shortcuts.get(model, model)
    compatibility = get_compatibility()
    version = get_version(model_name, compatibility)
    dl = download_model(dl_tpl.format(m=model_name, v=version))
    # Returns 0 if download was successful
    if dl != 0:
        return False

    # Refresh sys.path so we can import the installed package
    import site
    reload(site)
    reload(pkg_resources)
    return True
