Pimlico documentation
=====================

[Pimlico documentation](http://pimlico.readthedocs.io/en/latest/) 
is provided using [Sphinx](http://www.sphinx-doc.org/en/master/).
All configuration for the automatic building is provided here.

You can build the docs as described below and find the output in the `_build/html` directory. Most 
of the time, you'll just want to consult the [online documentation](http://pimlico.readthedocs.io/en/latest/), 
which is updated automatically when code is committed to Git.

**Tutorials and core documentation** are provided as ReST files.

* Run `make html`

Docs for **built-in Pimlico modules** are built automatically from the `ModuleInfo` that defines the module.

* Run `make modules` and then `make html`

**API** docs are built automatically using 
[Sphinx's apidoc tool](http://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html).

* Run `make api` and then `make html`

