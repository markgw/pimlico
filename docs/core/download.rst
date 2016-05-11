===================
Downloading Pimlico
===================

Pimlico is available for download from `its Gitlab page <https://gitlab.com/markgw/pimlico>`_.

If you're starting a new project using Pimlico, you'll want to download either
`the latest release <https://gitlab.com/markgw/pimlico/tags>`_ or the bleeding edge version,
`from the homepage <https://gitlab.com/markgw/pimlico>`_ (which might be a bit less stable).

Simply download the whole source code as a .zip or .tar.gz file and uncompress it. This will produce a directory
called `pimlico`, followed by a long incomprehensible string, which you can renamed simply `pimlico`.

No matter what you want to do with Pimlico, you'll need to fetch a few basic dependencies, which you can do with:

.. code-block:: bash

    cd pimlico/lib/python
    make core

See :doc:`/guides/setup` for more on getting started with Pimlico.
