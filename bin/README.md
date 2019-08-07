Command-line scripts
====================

These provide the main command-line interface to Pimlico. The most important one is `pimlico.sh`.

The test scripts use a special test virtual environment, not one of those created in `/lib/virtualenv/`. They each have a version with a `-2` suffix, which runs the tests in a Python 2 virtual environment, rather than the Python 3 default.

* `pimlico.sh`  
**Main command-line interace** to Pimlico. This calls the main Python front-end script via the configured 
Python interpreter. It uses `python` (in this directory) to ensure that the correct interpreter is used 
and config one if necessary.

* `python`  
Wrapper around the **Python interpreter** used by Pimlico. You can also use this directly, if you want to 
run Python scripts or a shell in the same environment used when Pimlico is run.

* `create_venv.sh`  
Create a new virtual environment that can be used to run Pimlico pipelines. 
By default, a single virtual environment called `default` is created the first time you run Pimlico. However, you may wish to use this to create others, if you need multiple Python software environments. You can then use it by naming it in an environment variable `PIMENV=<name>` before the `pimlico.sh` command.

* `test/test_pipeline.sh`  
Interface for **running module tests**. These consist of small pipelines, distributed with any necessary 
data and config, designed to test specific build-in modules. Since much Pimlico code is either core modules 
or difficult to run and test outside the context of a pipeline, these tests largely take the place of 
unit tests for the codebase. 
  * See the `test` directory and the `pimlico.test.pipeline` module.

* `test/all_tests.sh`  
Run all **unit tests**. Note that Pimlico does not have many unit tests. More may be added in future, but 
the bulk of testing is done via module tests.
  * See `test_pipeline.sh`