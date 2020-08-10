Running someone else's pipeline
===============================

This guide takes you through what to do if you have received someone else's
code for a Pimlico project and would like to run it.

This guide is written for Unix/Mac users. You'll need to make some adjustments
if using another OS.

What you've got
---------------

Hopefully got at least a pipeline config file. This will have the
extension ``.conf``. In the examples below, we'll use the name
``myproject.conf``.

You've probably got a whole directory, with some subdirectories, containing
this config file (or even several) together with other related files –
datasets, code, etc. This top-level directory is what we'll refer to
as the *project root*.

The project may include some code, probably defining some custom Pimlico
module types and datatypes. If all is well, you won't need to delve into
this, as its location will be given in the config file and Pimlico will
take care of the rest.

Getting Pimlico
---------------

You hopefully didn't receive the whole Pimlico codebase together with
the pipeline and code. It's recommended not to distribute Pimlico,
as it can be fetched automatically for a given pipeline.

You'll need Python installed.

Download the
`Pimlico bootstrap script from here <https://raw.githubusercontent.com/markgw/pimlico/master/admin/bootstrap.py>`_
and put it in the project root.

Now run it:

.. code-block:: sh

   python bootstrap.py myproject.conf

The bootstrap script will look in the config file to work out what version
of Pimlico to use and then download it.

If this works, you should now be able to run Pimlico.

Using the bleeding edge code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the bootstrap script will fetch a release of Pimlico that the
config file declares as being that which it was built with.

If you want the very latest version of Pimlico, with all the dangers that
entails and with the caveat that it might not work with the pipeline you're
trying to run, you can tell the bootstrap script to checkout Pimlico
from its Git repository.

.. code-block:: sh

   python bootstrap.py --git myproject.conf

Running Pimlico
---------------

Perhaps the project root contains a (link to a) script called ``pimlico.sh``.

If not, create one like this:

.. code-block:: sh

   ln -s pimlico/bin/pimlico.sh .

Now run ``pimlico.sh`` with the config file as an argument, issuing the :doc:`command_status`
command to see the contents of the pipeline:

.. code-block:: sh

   ./pimlico.sh myproject.conf status

Pimlico will now run and set itself up, before proceeding with your command and showing
the pipeline status. This might take a bit of time. It will install a Python
virtual environment and some basic packages needed for it to run.

