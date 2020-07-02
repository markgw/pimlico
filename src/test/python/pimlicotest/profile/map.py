"""
Profiling of document map module execution.

I'm trying to get to the bottom of what's taking most time when executing
document map modules, to work out how we can reduce overheads and speed
up execution.

.. todo::

   This is unfinished: continue working on it.

"""
import os
from urllib.request import urlretrieve
from zipfile import ZipFile

from pimlico import TEST_STORAGE_DIR

BBC_NEWS_URL = "http://mlg.ucd.ie/files/datasets/bbc-fulltext.zip"


def profile_doc_map():
    # TODO:
    #  - Create a pipeline that reads in the BBC corpus and applies tokenization
    #  - Wrap the pipeline execution code to load a profiler
    #  - Investigate what is taking most time: e.g.
    pass


def get_bbc_corpus():
    """
    Download BBC News corpus, a small corpus, but larger than our tiny
    test corpora.

    """
    bbc_news_dir = os.path.join(TEST_STORAGE_DIR, "bbc_news")
    corpus_dir = os.path.join(bbc_news_dir, "bbc")
    if os.path.exists(corpus_dir):
        # Corpus already available
        return corpus_dir

    archive_path = os.path.join(bbc_news_dir, "bbc_news.zip")
    if os.path.exists(archive_path):
        print("Archive already exists at {}".format(archive_path))
    else:
        print("Downloading BBC news corpus...")
        urlretrieve(BBC_NEWS_URL, archive_path)
    print("Extracting corpus to {}".format(bbc_news_dir))
    os.makedirs(bbc_news_dir)
    with ZipFile(archive_path, "r") as zf:
        zf.extractall(bbc_news_dir)
    os.remove(archive_path)
    return corpus_dir


if __name__ == "__main__":
    corpus_dir = get_bbc_corpus()
    print("Using BBC corpus in {}".format(corpus_dir))


PIPELINE = """
[pipeline]
name=test_map_profile
release=latest
python_path=%(project_root)s/src/python

"""
