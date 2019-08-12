.. _test-config-collect_files.conf:

collect\_files
~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=collect_files
   release=latest
   
   # Read in some named file datasets
   # This could be, for example, the output of the stats module
   [named_files1]
   type=NamedFileCollection
   filenames=text_file.txt
   dir=%(test_data_dir)s/datasets/named_files1
   
   [named_files2]
   type=NamedFileCollection
   filenames=data.bin,text_file.txt
   dir=%(test_data_dir)s/datasets/named_files2
   
   [collect]
   type=pimlico.modules.utility.collect_files
   input=named_files1,named_files2


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.utility.collect_files`
    

