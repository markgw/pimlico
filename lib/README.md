External libraries
==================

Various external libraries used by Pimlico live here.

* `virtualenv`  
Most libraries used by Pimlico are Python libraries that can be installed using Pip. 
Most of the time, you don't need to know anything about this, as Pimlico will automatically 
configure a virtualenv (in a subdirectory or this directory) to run Python and then automatically install all 
libraries within it.

* `libutils`  
Some tools for managing libraries, called by Pimlico as necessary. They are separate from the main 
Pimlico codebase so that they can be called independently early on in the bootstrapping process, before Pimlico 
has been configured.

* `java`  
**Compiled external Java libraries**. Generally these will be automatically fetched by Pimlico when installing 
software dependencies.

* `bin`  
**Compiled external libraries**.
The C&C compiler is an odd case of this, which requires some manual installation. See `bin/README_CANDC` for 
instructions.

* `test_env`  
Special virtualenv that will be created if you run **module tests**. (Otherwise, this won't exist.)