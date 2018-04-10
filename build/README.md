Compiled code
=============

Pimlico is mostly written in Python, so doesn't require compilation. Certain small parts of 
the code that provide interfaces to code in other languages require compilation.

Currently, the only case is **Java code**, though other code may require building in future. 
Java interaces are provided as compiled jar files in this directory, so you generally won't 
need to compile any code yourself. The jar files will be executed directly by build-in 
Pimlico modules, so you probably don't need to concern yourself with what's in this 
directory at all.
