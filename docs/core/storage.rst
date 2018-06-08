.. _data-storage:

================
  Data storage
================


Pimlico needs to know where to put and find output files as it executes, in order to
store data and pass it between modules. On any particular system running Pimlico,
multiple locations (**stores**) may be used as storage and Pimlico will check all of them when
it's looking for a module's data.


Single store
============
Let's start with a simple setup with just one store. A setting ``store`` in the local config
(see :ref:`local-config`) specifies the root directory of this store. This applies to all Pimlico
pipelines you run on this system and Pimlico will make sure that different pipelines don't interfere
with each other's output (provided you give them different names).

When you run a pipeline module, its output will be stored in a subdirectory specific to that pipeline
and that module with the store's root directory. When Pimlico needs to use that data as input to
another module, it will look in the appropriate directory within the store.

Multiple stores
===============
For various reasons, you may wish to store Pimlico data in multiple locations.

For example, one common scenario is that you have access to a disk
that is fast to write to (call it *fast-disk*), but not
very big, and another disk (e.g. over a network filesystem) that has lots of space, but is slower
(call it *big-disk*).
You therefore want Pimlico to output its data, much of which might only be used fleetingly and then
no longer needed, to *fast-disk*, so the processing runs quickly. Then, you want to move the output
from certain modules over to *big-disk*, to make space on *fast-disk*.

We can define two stores for Pimlico to use and give them names.
The first ("fast") will be used to output data to (just like
the sole store in the previous section). The second ("big"), however, will also be checked for module
data, meaning that we can move data from "fast" to "big" whenever we like.

Instead of using the ``store`` parameter in the local config, we use multiple ``store_<name>`` parameters.
One of them (the first one, or the one given by ``store`` with no name, if you include that) we be
treated as the default output store.

Specific the locations in the local config like this:

.. code-block:: ini

    store_fast=/path/to/fast/store
    store_big=/path/to/big/store

Remember, these paths are not specific to a pipeline: all pipelines will use different
subdirectories of these ones.

To check what stores you've got in your current configuration, use the :ref:`command_stores` command.


Moving data between stores
==========================
Say you've got a two-store setup like in the previous example. You've now run a module that
produces a lot of output and want to move it to your big disk and have Pimlico read it from
there.

You don't need to replicate the directory structure yourself and move module output between
stores. Pimlico has a command :ref:`command_movestores` to do this for you. Specify the name of
the store you want to move data to (``big`` in this case) and the names or numbers of the modules
whose data you want to move.

Once you've done that, Pimlico should continue to behave as it did before, just as if the
data was still in its original location.
