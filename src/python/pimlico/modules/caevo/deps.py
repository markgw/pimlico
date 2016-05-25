import shutil
import subprocess

import os
from pimlico import JAVA_LIB_DIR, MODEL_DIR

from pimlico.core.dependencies.base import SystemCommandDependency, InstallationError
from pimlico.core.dependencies.java import PimlicoJavaLibrary, JavaDependency, argparse4j_dependency
from pimlico.utils.filesystem import extract_archive
from pimlico.utils.web import download_file


class CaevoDependency(JavaDependency):
    def __init__(self):
        super(CaevoDependency, self).__init__("CAEVO", classes=["caevo.SieveDocument"],
                                              jars=["caevo-1.1.jar", "caevo-1.1-jar-with-dependencies.jar"])

    def dependencies(self):
        return [SystemCommandDependency("Maven", "mvn -v")]

    def installable(self):
        return True

    def install(self, trust_downloaded_archives=False):
        # We know that Maven is available
        src_dir = os.path.join(JAVA_LIB_DIR, "caevo_src")
        if not os.path.exists(src_dir) or not trust_downloaded_archives:
            # Fetch the source code
            archive_code = "8cfc810baff833063da9b423ef7a36983b3ab0e2"
            archive_url = "https://github.com/nchambers/caevo/archive/%s.zip" % archive_code
            print "Fetching archive from %s" % archive_url
            download_file(archive_url, os.path.join(JAVA_LIB_DIR, "caevo.zip"))
            # Extract the archive
            print "Extracting"
            extract_archive(os.path.join(JAVA_LIB_DIR, "caevo.zip"), JAVA_LIB_DIR)
            # Rename the dir to something sensible
            os.rename(os.path.join(JAVA_LIB_DIR, "caevo-%s" % archive_code), src_dir)
            # Get rid of the archive now we've extracted it
            os.remove(os.path.join(JAVA_LIB_DIR, "caevo.zip"))

        if not os.path.exists(os.path.join(src_dir, "src", "test", "resources", "wordnet", "dict")):
            # Before compiling, run the script to get hold of the wordnet dictionaries
            print "Fetching WordNet dictionaries"
            try:
                subprocess.check_output(
                    ["sh", os.path.join(src_dir, "download-wordnet-dictionaries")], cwd=src_dir, shell=True)
            except subprocess.CalledProcessError, e:
                raise InstallationError("could not fetch WordNet dictionaries using CAEVO's script: %s" % e)

        # Use Maven to compile the code
        print "Compiling Caevo with Maven"
        try:
            subprocess.check_output(["mvn", "compile"], cwd=src_dir, shell=True)
        except subprocess.CalledProcessError, e:
            raise InstallationError("error compiling CAEVO with Maven: %s" % e)

        # Package Caevo up, together with dependencies, in jar
        print "Packaging Caevo in jar"
        package_env = os.environ.copy()
        package_env["JWNL"] = os.path.join(src_dir, "src", "test", "resources", "jwnl_file_properties.xml")
        try:
            subprocess.check_output(["mvn", "package", "assembly:single"], cwd=src_dir, shell=True, env=package_env)
        except subprocess.CalledProcessError, e:
            raise InstallationError("error compiling CAEVO with Maven: %s" % e)
        os.rename(os.path.join(src_dir, "target", "caevo-1.1-jar-with-dependencies.jar", JAVA_LIB_DIR))
        os.rename(os.path.join(src_dir, "target", "caevo-1.1.jar", JAVA_LIB_DIR))

        # Put sieve configs in models dir
        print "Copying model files"
        model_dir = os.path.join(MODEL_DIR, "caevo")
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        for filename in os.listdir(src_dir):
            if filename.endswith(".sieves"):
                shutil.copy(os.path.join(src_dir, filename), model_dir)
        # And wordnet files
        shutil.copytree(os.path.join(src_dir, "src", "test", "resources", "wordnet", "dict"), model_dir)

        # Get rid of the source code
        print "Cleaning up"
        shutil.rmtree(src_dir)


caevo_dependency = CaevoDependency()


caevo_wrapper_dependency = PimlicoJavaLibrary(
    "caevo", classes=["pimlico.caevo.CaevoGateway"],
    # To run the wrapper, you need Caevo and Argparse4j on the classpath
    additional_jars=caevo_dependency.jars+argparse4j_dependency.jars
)
