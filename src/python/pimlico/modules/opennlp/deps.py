import os
from pimlico import JAVA_BUILD_JAR_DIR

from pimlico.core.dependencies.java import JavaDependency, py4j_dependency, JavaJarsDependency, argparse4j_dependency

OPENNLP_VERSION = "1.5.3"
OPENNLP_URL = "http://apache.mesi.com.ar//opennlp/opennlp-{v}/apache-opennlp-{v}-bin.tar.gz".format(v=OPENNLP_VERSION)


opennlp_dependency = JavaJarsDependency(
    "OpenNLP",
    [
        (jar_name, "{url}->apache-opennlp-{v}/lib/{jar}".format(url=OPENNLP_URL, v=OPENNLP_VERSION, jar=jar_name))
        for jar_name in [
            "opennlp-maxent-3.0.3.jar",
            "opennlp-tools-{v}.jar".format(v=OPENNLP_VERSION),
            "opennlp-uima-{v}.jar".format(v=OPENNLP_VERSION),
            "jwnl-1.3.3.jar",
        ]
    ]
)


def py4j_wrapper_dependency(test_class_name):
    return JavaDependency("OpenNLP wrapper", jars=[os.path.join(JAVA_BUILD_JAR_DIR, "opennlp.jar")],
                          classes=[test_class_name],
                          dependencies=[argparse4j_dependency, py4j_dependency, opennlp_dependency])