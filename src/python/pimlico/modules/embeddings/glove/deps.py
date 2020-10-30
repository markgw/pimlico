
import os
import shutil
import subprocess
from zipfile import ZipFile

from pimlico.core.dependencies.licenses import APACHE_V2

from pimlico import LIB_DIR
from pimlico.core.dependencies.base import SoftwareDependency
from pimlico.utils.web import download_file


class GloVeDependency(SoftwareDependency):
    """
    Allows GloVe to be installed locally within the Pimlico environment.

    Requires GCC to be installed on the system.

    """
    GLOVE_URL = "https://github.com/stanfordnlp/GloVe/archive/master.zip"

    def __init__(self):
        super(GloVeDependency, self).__init__(
            "glove",
            homepage_url="https://nlp.stanford.edu/projects/glove/",
            license=APACHE_V2)

    @property
    def glove_path(self):
        return os.path.join(LIB_DIR, "glove")

    @property
    def build_path(self):
        return os.path.join(self.glove_path, "build")

    def available(self, local_config):
        return os.path.exists(os.path.join(self.build_path, "glove"))

    def installable(self):
        try:
            subprocess.check_call(["gcc", "--version"], shell=False, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return False
        return True

    def install(self, local_config, trust_downloaded_archives=False):
        if os.path.exists(self.glove_path):
            shutil.rmtree(self.glove_path)

        # Download the code from the GloVe repo
        archive_path = os.path.join(LIB_DIR, "master.zip")
        print("Downloading GloVe code from {}".format(self.GLOVE_URL))
        download_file(self.GLOVE_URL, archive_path)
        # Unzip the code
        with ZipFile(archive_path, mode="r") as zipf:
            zipf.extractall(LIB_DIR)
        os.remove(archive_path)
        # Rename the directory
        shutil.move(os.path.join(LIB_DIR, "GloVe-master"), self.glove_path)
        print("GloVe code available in {}".format(self.glove_path))

        # Now compile the code
        print("Compiling GloVe tool")
        try:
            subprocess.check_call("make", cwd=self.glove_path, shell=True)
        except subprocess.CalledProcessError as e:
            print("GloVe compilation failed with status {}: {}".format(e.returncode, e))
            raise
        print("GloVe compilation complete: tools available in {}".format(self.build_path))


glove_dependency = GloVeDependency()
