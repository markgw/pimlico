Pimlico test data and config
============================

Pimlico provides tests (among other sorts) in the form of small pipelines, equipped with 
 all the data required to run them. Typically, a test pipeline is designed to test exactly 
 one module or datatype, though of course others may be involved (e.g. input datatypes to 
 the module being tested).

See the `pimlico.test.pipeline` Python module for more details.

The `data` directory contains the test pipeline config files and small demo datasets.

The `storage` directory should generally be empty and is used as a temporary storage 
location for pipeline output when the tests are run.
