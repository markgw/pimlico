# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError


def check_corenlp_dependencies(module_name):
    """
    Check dependencies in the style of module dependency checkers and return a list of the missing
    dependencies in the form they use. Designed to make it easy for all modules that use CoreNLP to
    check the basic deps.
    """
    missing_dependencies = []
    try:
        class_name = "edu.stanford.nlp.pipeline.StanfordCoreNLPServer"
        try:
            check_java_dependency(class_name)
        except DependencyError, e:
            if e.stderr is not None:
                extra_err = ". (Error: %s)" % e.stderr.splitlines()[0]
            else:
                extra_err = ""
            missing_dependencies.append(("CoreNLP", module_name,
                                         "Couldn't load %s. Install Stanford CoreNLP libraries in Java lib dir using "
                                         "'make corenlp'%s" % (class_name, extra_err)))
    except DependencyCheckerError, e:
        missing_dependencies.append(("Java dependency checker", module_name, str(e)))

    # We depend on the requests library
    try:
        import requests
    except ImportError:
        missing_dependencies.append(("Python requests library", module_name,
                                     "Install together with all CoreNLP python deps in Python lib dir using "
                                     "'make stanford'"))
    return missing_dependencies
