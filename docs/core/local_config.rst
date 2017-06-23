.. _local-config:

=======================
  Local configuration
=======================
As well as knowing about the pipeline you're running, Pimlico also needs to know some things about the setup of the
system on which you're running it. This is completely independent of the pipeline config: the same pipeline can
be run on different systems with different local setups.

A couple of settings must always be provided for Pimlico: the **long-term** and **short-term stores** (see
:ref:`data-stores` below). Other system settings may be specified as necessary. (At the time of writing, there
aren't any, but they will be documented here as they arise.) See :ref:`other-local-config` below.

Specific modules may also have system-level settings. For example, a module that calls an external tool may need
to know the location of that tool, or how much memory it can use on this system. Any that apply to the built-in
Pimlico modules are listed below in :ref:`built-in-module-local-config`.

Local config file location
==========================
Pimlico looks in various places to find the local config settings. Settings are loaded in a particular order,
overriding earlier versions of the same setting as we go
(see :meth:`pimlico.core.config.PipelineConfig.load_local_config`).

Settings are specified with the following order of precedence (those later override the earlier)::

   local config file < host-specific config file < cmd-line overrides

Most often, you'll just specify all settings in the main local config file. This is a file in your home directory
named ``.pimlico``. This must exist for Pimlico to be able to run at all.

Host-specific config
--------------------
If you share your home directory between different computers (e.g. a networked filesystem), the above setup could
cause a problem, as you may need a different local config on the different computers. Pimlico allows you to
have special config files that only get read on machines will a particular hostname.

For example, say I have two computers, ``localbox`` and ``remotebox``, which share a home directory. I've created my
``.pimlico`` local config file on ``localbox``, but need to specify a different storage location on ``remotebox``.
I simply create another config file called ``.pimlico_remotebox``[#hostname]_. Pimlico will load first the
basic local config in ``.pimlico`` and then override those settings with what it reads from the host-specific
config file.

You can also specify a hostname prefix to match. Say I've got a whole load of computers I want to be able to
run on, with hostnames ``remotebox1``, ``remotebox2``, etc. If I create a config file called ``.pimlico_remotebox-``,
it will be used on all of these hosts.

Command-line overrides
----------------------
Occasionally, you might want to specify a local config setting just for one run of Pimlico. Use the
``--override-local-config`` (or ``-l``) to specify a value for an individual setting in the form ``setting=value``.
For example:

.. code:: sh

   ./pimlico.sh mypipeline.conf -l somesetting=5 run mymodule

If you want to override multiple settings, simply use the option multiple times.

Custom location
---------------
If the above solutions don't work for you, you can also explicitly specify on the command line an alternative
location from which to load the local config file that Pimlico typically expects to find in ``~/.pimlico``.

Use the ``--local-config`` parameter to give a filename to use instead of the ``~/.pimlico``.

For example, if your home directory is shared across servers and the above hostname-specific config solution
doesn't work in your case, you can fall back to pointing Pimlico at your own host-specific config file.

.. _data-stores:

Long-term and short-term stores
===============================
Pimlico needs to know where to put and find output files as it executes.
Settings are given in the local config, since they apply to all Pimlico pipelines you run and may vary from
system to system.
Note that Pimlico will make sure that different pipelines don't interfere
with each other's output (provided you give them different names): all pipelines store their output and look
for their input within these same base locations.

The **short-term store** should be on a disk that's as fast as possible to write to. For example, avoid using an NFS
disk. It needs to be large enough to store output between pipeline stages, though you can easily move
output from earlier stages into the long-term store as you go along.

The **long-term store** is where things are typically put at the end of
a pipeline. It therefore doesn't need to be super-fast to access, but you may want it to be in a location that gets
backed up, so you don't lose your valuable output.

For a simple setup, these could be just two subdirectories of the same directory, or actually the same directory.
However, it can be useful to distinguish them.

Specific the locations in the local config like this:

.. code-block:: ini

    long_term_store=/path/to/long-term/store
    short_term_store=/path/to/short-term/store

Remember, these paths are not specific to a pipeline: all pipelines will use different subdirectories of these ones.

.. _other-local-config:

Other Pimlico settings
======================
In future, there will no doubt be more settings that you can specify at the system level for Pimlico. These
will be documented here as they arise.

.. _built-in-module-local-config:

Settings for built-in modules
=============================
Specific modules may consult the local config to allow you to specify settings for them. We cannot document them here
for all modules, as we don't know what modules are being developed outside the core codebase. However, we can
provide a list here of the settings consulted by built-in Pimlico modules.

There aren't any yet, but they will be listed here as they arise.

.. rubric:: Footnotes:

.. [#hostname] This relies on Python being aware of the hostname of the computer. Pimlico uses ``socket.gethostname()``
               to find out the current machine's hostname, which in this example should return ``remotebox``. On Linux,
               you can check what this is using the ``hostname`` command.
