# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from pimlico.core.dependencies.java import JavaJarsDependency
from pimlico.core.dependencies.python import PythonPackageOnPip


corenlp_jar_dependency = JavaJarsDependency(
    "CoreNLP",
    [
        # All of these jars come in the same zip archive
        # It will only be downloaded once by the installer
        (
            "stanford-corenlp-3.6.0.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/stanford-corenlp-3.6.0.jar"
        ),
        (
            "stanford-corenlp-3.6.0-models.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/stanford-corenlp-3.6.0-models.jar"
        ),
        (
            "ejml-0.23.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/ejml-0.23.jar"
        ),
        (
            "javax.json.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/javax.json.jar"
        ),
        (
            "joda-time.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/joda-time.jar"
        ),
        (
            "jollyday.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/jollyday.jar"
        ),
        (
            "protobuf.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/protobuf.jar"
        ),
        (
            "slf4j-simple.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/slf4j-simple.jar"
        ),
        (
            "slf4j-api.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/slf4j-api.jar"
        ),
        (
            "xom.jar",
            "http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip"
            "->stanford-corenlp-full-2015-12-09/xom.jar"
        ),
    ],
    # Check that installation has worked by trying to load the server class
    classes=["edu.stanford.nlp.pipeline.StanfordCoreNLPServer"]
)

# A collection of dependencies for using CoreNLP
corenlp_dependencies = [
    corenlp_jar_dependency,
    # We also need the requests library: install using pip
    PythonPackageOnPip("requests", "Requests"),
]
