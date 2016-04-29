"""
Scikit-learn tools

`Scikit-learn <http://scikit-learn.org/stable/>`_ ('sklearn')
provides easy-to-use implementations of a large number of machine-learning methods, based on
`Numpy/Scipy <http://scipy.org/>`_.

You can build Numpy arrays from your corpus using the :mod:`feature processing tools <pimlico.modules.features>`
and then use them as input to Scikit-learn's tools using the modules in this package.

"""


def check_sklearn_dependency(module_name):
    """
    Check that Scikit-Learn is installed and importable.

    """
    missing_dependencies = []

    try:
        import sklearn
    except ImportError:
        missing_dependencies.append(("scikit-learn", module_name, "Install Scikit-Learn systemwide. E.g. "
                                                                  "'apt-get install python-sklearn' or "
                                                                  "'pip install -U scikit-learn'"))
    return missing_dependencies
