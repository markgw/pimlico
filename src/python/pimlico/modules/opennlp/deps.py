# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os

from pimlico.core.dependencies.licenses import APACHE_V2, NOT_RELEVANT

from pimlico import JAVA_BUILD_JAR_DIR

from pimlico.core.dependencies.java import JavaDependency, py4j_dependency, JavaJarsDependency, argparse4j_dependency

OPENNLP_VERSION = "1.9.2"
OPENNLP_URL = "http://mirror.netinch.com/pub/apache/opennlp/opennlp-{v}/apache-opennlp-{v}-bin.tar.gz".format(v=OPENNLP_VERSION)


opennlp_dependency = JavaJarsDependency(
    "OpenNLP",
    [
        (jar_name, "{url}->apache-opennlp-{v}/lib/{jar}".format(url=OPENNLP_URL, v=OPENNLP_VERSION, jar=jar_name))
        for jar_name in [
            "opennlp-tools-{v}.jar".format(v=OPENNLP_VERSION),
            "opennlp-uima-{v}.jar".format(v=OPENNLP_VERSION),
        ]
    ] + [
        # Not everything necessarily needs Guava, but we tend to use it a lot, so include in all OpenNLP dep sets
        ("guava.jar", "http://search.maven.org/remotecontent?filepath=com/google/guava/guava/23.0/guava-23.0.jar"),
    ],
    homepage_url="https://opennlp.apache.org/",
    license=APACHE_V2
)


def py4j_wrapper_dependency(test_class_name):
    return JavaDependency("OpenNLP wrapper", jars=[os.path.join(JAVA_BUILD_JAR_DIR, "opennlp.jar")],
                          classes=[test_class_name],
                          dependencies=[argparse4j_dependency, py4j_dependency, opennlp_dependency],
                          license=NOT_RELEVANT)
