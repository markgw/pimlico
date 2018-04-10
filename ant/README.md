Java build config
=================

Java Ant build files for the small Java libraries used by certain build-in modules. These typically 
allow the modules to access Java toolkits, like OpenNLP, by providing an API on the Java side that 
the Pimlico module can set going and then issue calls to.

Pimlico is mostly written in Python and these small Java libraries are included in built form in the 
codebase, so generally you won't need to use these build files, unless you're developing the Java 
interfaces.