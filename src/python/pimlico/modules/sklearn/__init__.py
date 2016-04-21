
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
