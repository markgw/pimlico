======================
  Multistage modules
======================

Multistage modules are used to encapsulate a module than is executed in several consecutive runs. You can think
of each stage as being its own module, but where the whole sequence of modules is always executed together.
The multistage module simply chains together these individual modules so that you only include a single
module instance in your pipeline definition.

One common example of a use case for multistage modules is where some fairly time-consuming preprocessing needs
to be done on an input dataset. If you put all of the processing into a single module, you can end up in an
irritating situation where the lengthy data preprocessing succeeds, but something goes wrong in the main execution
code. You then fix the problem and have to run all the preprocessing again.

Most obvious solution to this is to separate the preprocessing and main execution into two separate modules. But
then, if you want to reuse you module sometime in the future, you have to remember to always put the preprocessing
module before the main one in your pipeline (or infer this from the datatypes!). And if you have more than these
two modules (say, a sequence of several, or preprocessing of several inputs) this starts to make pipeline
development frustrating.

A multistage module groups these internal modules into one logical unit, allowing them to be used together by
including a single module instance and also to share parameters.

Defining a multistage module
============================

Component stages
----------------

The first step in defining a multistage module is to define its individual stages.
These are actually defined in exactly the same way as normal modules.
(This means that they can also be used separately.)

If you're writing these modules specifically to provide the stages of your multistage module (rather than tying
together already existing modules for convenience), you probably want to put them all in subpackages.

For an ordinary module, :ref:`we used the directory structure <guides/module>`::

    src/python/myproject/modules/
        __init__.py
        mymodule/
            __init__.py
            info.py
            execute.py

Now, we'll use something like this::

    src/python/myproject/modules/
        __init__.py
        my_ms_module/
            __init__.py
            info.py
            module1/
                __init__.py
                info.py
                execute.py
            module2/
                __init__.py
                info.py
                execute.py

Note that `module1` and `module2` both have the typical structure of a module definition: an `info.py` to define
the module-info, and an `execute.py` to define the executor. At the top level, we've just got an `info.py`. It's
in here that we'll define the multistage module. We don't need an `execute.py` for that, since it just ties together
the other modules, using their executors at execution time.

Multistage module-info
----------------------

With our component modules that constitute the stages defined, we now just need to tie them together. We do this
by defining a module-info for the multistage module in its `info.py`. Instead of subclassing
:cls:`~pimlico.core.modules.BaseModuleInfo`, as usual, we create the `ModuleInfo` class using the factory function
:fn:`~pimlico.core.modules.multistage.multistage_module`.

In other respects, this module-info works in the same way as usual: it's a class (return by the factory) called
`ModuleInfo` in the `info.py`.

:fn:`~pimlico.core.modules.multistage.multistage_module` takes two arguments: a module name (equivalent to
the `module_name` attribute of a normal module-info) and a list of instances of
:cls:`~pimlico.core.modules.multistage.ModuleStage`.

Connecting inputs and outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Connections between the outputs and inputs of the stages work in a very similar way to connections between
module instances in a pipeline. The same type checking system is employed and data is passed between the stages
(i.e. between consecutive executions) as if the stages were separate modules.

Each stage is defined as an instance of :cls:`~pimlico.core.modules.multistage.ModuleStage`:

.. code-block:: py

   [
       ModuleStage("stage_name", TheModuleInfoClass, connections=[...], output_connections=[...])
   ]

The parameter `connections` defines how the stage's inputs are connected up to either the outputs of previous stages
or inputs to the multistage module.
Just like in pipeline config files, if no explicit input connections are given, the default input to a stage is
connected to the default output from the previous one in the list.

There are two classes you can use to define input connections.

:cls:`~pimlico.core.modules.multistage.InternalModuleConnection`
   This makes an explicit connection to the output of another stage.

   You must specify the name of the input (to this stage) that you're connecting. You may specify the
   name of the output to connect it to (defaults to the default output). You may also give the name of the stage that
   the output comes from (defaults to the previous one).

   .. code-block:: py

      [
          ModuleStage("stage1", FirstInfo),
          # FirstInfo has an output called "corpus", which we connect explicitly to the next stage
          # We could leave out the "corpus" here, if it's the default output from FirstInfo
          ModuleStage("stage2", SecondInfo, connections=[InternalModuleConnection("data", "corpus")]),
          # We connect the same output from stage1 to stage3
         ModuleStage("stage3", ThirdInfo, connections=[InternalModuleConnection("data", "corpus", "stage1")]),
      ]

:cls:`~pimlico.core.modules.multistage.ModuleInputConnection`:
   This makes a connection to an input to the whole multistage module.

   Note that you don't have to explicitly define the multistage module's inputs anywhere: you just mark certain
   inputs to certain stages as coming from outside the multistage module, using this class.

   .. code-block:: py

      [
          ModuleStage("stage1", FirstInfo,  [ModuleInputConnection("raw_data")]),
          ModuleStage("stage2", SecondInfo, [InternalModuleConnection("data", "corpus")]),
          ModuleStage("stage3", ThirdInfo,  [InternalModuleConnection("data", "corpus", "stage1")]),
      ]

   Here, the module type `FirstInfo` has an input called `raw_data`. We've specified that this needs to come in
   directly as an input to the multistage module -- when we use the multistage module in a pipeline, it must be
   connected up with some earlier module.

   The multistage module's input created by doing this will also have the name `raw_data` (specified using a parameter
   `input_raw_data` in the config file). You can override this, if you want to use a different name:

   .. code-block:: py

      [
          ModuleStage("stage1", FirstInfo,  [ModuleInputConnection("raw_data", "data")]),
          ModuleStage("stage2", SecondInfo, [InternalModuleConnection("data", "corpus")]),
          ModuleStage("stage3", ThirdInfo,  [InternalModuleConnection("data", "corpus", "stage1")]),
      ]

   This would be necessary if two stages both had inputs called `raw_data`, which you want to come from different
   data sources. You would then simply connect them to different inputs to the multistage module:

   .. code-block:: py

      [
          ModuleStage("stage1", FirstInfo,  [ModuleInputConnection("raw_data", "first_data")]),
          ModuleStage("stage2", SecondInfo, [ModuleInputConnection("raw_data", "second_data")]),
          ModuleStage("stage3", ThirdInfo,  [InternalModuleConnection("data", "corpus", "stage1")]),
      ]

   Conversely, you might deliberately connect the inputs from two stages to the same input to the multistage module,
   by using the same multistage input name twice. (Of course, the two stages are not required to have overlapping input
   names for this to work.)
   This will result in the multistage just requiring one input, which get used by both stages.

   .. code-block:: py

      [
          ModuleStage("stage1", FirstInfo,
                      [ModuleInputConnection("raw_data", "first_data"), ModuleInputConnection("dict", "vocab")]),
          ModuleStage("stage2", SecondInfo,
                      [ModuleInputConnection("raw_data", "second_data"), ModuleInputConnection("vocabulary", "vocab")]),
          ModuleStage("stage3", ThirdInfo,  [InternalModuleConnection("data", "corpus", "stage1")]),
      ]

By default, the multistage module has just a single output: the default output of the last stage in the list.
You can specify any of the outputs of any of the stages to be provided as an output to the multistage module.
Use the `output_connections` parameter when defining the stage.

This parameter should be a list of instances of :cls:`~pimlico.core.modules.multistage.ModuleOutputConnection`.
Just like with input connections, if you don't specify otherwise, the multistage module's output will have the
same name as the output from the stage module. But you can override this when giving the output connection.

.. code-block:: py

   [
       ModuleStage("stage1", FirstInfo, [ModuleInputConnection("raw_data", "first_data")]),
       ModuleStage("stage2", SecondInfo, [ModuleInputConnection("raw_data", "second_data")],
                   output_connections=[ModuleOutputConnection("model")]),   # This output will just be called "model"
       ModuleStage("stage3", ThirdInfo,  [InternalModuleConnection("data", "corpus", "stage1"),
                   output_connections=[ModuleOutputConnection("model", "stage3_model")]),
   ]

Module options
~~~~~~~~~~~~~~

The parameters of the multistage module that can be specified when it is used in a pipeline config (those usually
defined in the `module_options` attribute) include all of the options to all of the stages. The option names are
simply `<stage_name>_<option_name>`.

So, in the above example, if `FirstInfo` has an option called `threshold`, the multistage module will have an
option `stage1_threshold`, which gets passed through to `stage1` when it is run.

.. note::

   There is a desirable possible feature here, which I have not got round to implementing yet.

   Often you might wish to specify one parameter to the multistage module that gets used by several stages.
   Say `stage2` had a `cutoff` parameter and we always wanted to use the same value as the `threshold` for `stage1`.
   Right now, you have to specify `stage1_threshold` and `stage2_cutoff` in you config file.

   It would be nice to have a way to declare in the multistage module creation that the multistage module should
   have a parameter `threshold`, which gets used as `stage1_threshold` and `stage2_cutoff`.

Running
=======

To run a multistage module once you've used it in your pipeline config,
you run one stage at a time, as if they were separate module instances.

Say we've used the above multistage module in a pipeline like so:

.. code-block:: ini

   [model_train]
   type=myproject.modules.my_ms_module
   stage1_threshold=10
   stage2_cutoff=10

The normal way to run this module would be to use the `run` command with the module name:

.. code-block:: bash

   ./pimlico.sh mypipeline.conf run model_train

If we do this, Pimlico will choose the next unexecuted stage that's ready to run (presumably `stage1` at this point).
Once that's done, you can run the same command again to execute `stage2`.

You can also select a specific stage to execute by using the module name `<ms_module_name>:<stage_name>`, e.g.
`model_train:stage2`. (Note that `stage2` doesn't actually depend on `stage1`, so it's perfectly plausible that
we might want to execute them in a different order.)

If you want to execute multiple stages at once, just use this scheme to specify each of them as a module name
for the run command. Remember, Pimlico can take any number of modules and execute them in sequence:

.. code-block:: bash

   ./pimlico.sh mypipeline.conf run model_train:stage1 model_train:stage2

Or, if you want to execute all of them, you can use the stage name `*` or `all` as a shorthand:

.. code-block:: bash

   ./pimlico.sh mypipeline.conf run model_train:all

Finally, if you're not sure what stages a multistage module has, use the module name `<ms_module_name>:?`. The run
command will then just output a list of stages and exit.
