Command-line scripts
====================

These provide the main command-line interface to Pimlico. The most important one is `pimlico.sh`.

* `pimlico.sh`  
**Main command-line interace** to Pimlico. This calls the main Python front-end script via the configured 
Python interpreter. It uses `python` (in this directory) to ensure that the correct interpreter is used 
and config one if necessary.

* `python`  
Wrapper around the **Python interpreter** used by Pimlico. You can also use this directly, if you want to 
run Python scripts or a shell in the same environment used when Pimlico is run.

* `test_pipeline.sh`  
Interface for **running module tests**. These consist of small pipelines, distributed with any necessary 
data and config, designed to test specific build-in modules. Since much Pimlico code is either core modules 
or difficult to run and test outside the context of a pipeline, these tests largely take the place of 
unit tests for the codebase. 
  * See the `test` directory and the `pimlico.test.pipeline` module.

* `all_tests.sh`  
Run all **unit tests**. Note that Pimlico does not have many unit tests. More may be added in future, but 
the bulk of testing is done via module tests.
  * See `test_pipeline.sh`