"""
Utilities for loading spaCy models.

NOTE: imports spaCy, so *only* import this from module execute.py files.

"""
import spacy
from spacy.cli.download import get_json, get_compatibility, get_version, download_model
from spacy import about
from importlib import reload
import pkg_resources


def load_spacy_model(model_name, log, local=False):
    """
    Try loading a spaCy model.

    :param model_name: model name or path to model
    :param local: True if the model is a local file, not a model name that can be
        downloaded from the spaCy archives
    :return: nlp
    """

    try:
        nlp = spacy.load(model_name)
    except IOError:
        # Couldn't load spacy model
        if not local:
            # If not loading from disk, we need to run the spacy download command
            log.info("Downloading the model '{}'".format(model_name))
            if not download_spacy_model(model_name):
                raise SpacyModelLoadError("Model could not be downloaded")
        else:
            raise
        # Now the model should be available
        nlp = spacy.load(model_name)
    return nlp


def download_spacy_model(model):
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


class SpacyModelLoadError(Exception):
    pass
