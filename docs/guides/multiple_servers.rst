==========================================
Running one pipeline on multiple computers
==========================================

Multiple servers
================
In most of the examples, we've been setting up a pipeline, with a config file, some source code and some
data, all on one machine. Then we run each module in turn, checking that it has all the software and
data that it needs to run.

But it's not unusual to find yourself needing to process a dataset across different computers. For example,
you have access to a server with lots of CPUs and one module in your pipeline would benefit greatly from
parallelizing lots of little tasks over them. However, you don't have permission to install software on
that server that you need for another module.

This is not a problem: you can simply put your config file and code on both machines. After running one
module on one machine, you copy over its output to the place on the other machine where Pimlico expects to
find it. Then you're ready to run the next module on the second machine.

Pimlico is designed to handle this situation nicely.

- **It doesn't expect software requirements for all modules to be satisfied before you can run any of them.**
  Software dependencies are checked only for modules about to be run and the code used to execute a module
  is not even loaded until you actually run the module.
- **It doesn't require you to execute your pipeline in order.**
  If the output from a module is available where it's expected to be, you can happily run any modules that
  take that data as input, even if the pipeline up to that point doesn't appear to have been executed (e.g.
  if it's been run on another machine).
- **It provides you with tools to make it easier to copy data between machines.**
  You can easily copy the output data from one module to the appropriate location on another server, so
  it's ready to be used as input to another module there.

Copying data between computers
==============================
Let's assume you've got your pipeline set up, with identical config files, on two computers: `server_a` and
`server_b`. You've run the first module in your pipeline, `module1`, on `server_a` and want to run the
next, `module2`, which takes input from `module1`, on `server_b`.

The procedure is as follows:

- **Dump** the data from the pipeline on `server_a`. This packages up the output data for a module in a
  single file.
- **Copy** the dumped file from `server_a` to `server_b`, in whatever way is most convenient, e.g., using
  `scp`.
- **Load** the dumped file into the pipeline on `server_b`. This unpacks the data directory for the file
  and puts it in Pimlico's data directory for the module.

For example, on `server_a`:

.. code-block:: sh

   $ ./pimlico.sh pipeline.conf dump module1
   $ scp ~/module1.tar.gz server_b:~/

Note that the `dump` command created a `.tar.gz` file in your home directory. If you want to put it somewhere
else, use the `--output` option to specify a directory. The file is named after the module that you're dumping.

Now, log into `server_b` and load the data.

.. code-block:: sh

   $ ./pimlico.sh pipeline.conf load ~/module1.tar.gz

Now `module1`'s output data is in the right place and ready for use by `module2`.

The `dump` and `load` commands can also process data for multiple modules at once. For example:

.. code-block:: sh

   $ mkdir ~/modules
   $ ./pimlico.sh pipeline.conf dump module1 ... module10 --output ~/modules
   $ scp -r ~/modules server_b:~/

Then on `server_b`:

.. code-block:: sh

   $ ./pimlico.sh pipeline.conf load ~/modules/*
