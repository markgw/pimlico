Pimlico codebase administration tools
=====================================

* `release.txt`  
Specifies the **current (bleeding edge) version identifier**. This file is consulted by version 
management routines to work out what version number to use for the latest version, when not 
using a specific release.

* `newproject.py`  
Script to **set up a new Pimlico project**, with the standard layout of directories, and fetch Pimlico itself.
The recommended way to start a new project using Pimlico is to download this Python file into a new 
directory, straight from the Git repository and run it. See getting-started docs for more guidance.

* `bootstrap.py`  
Bootstrapping script that **creates a basic Pimlico setup**, either for an existing config file, or for a new project.
This should be distributed with Pimlico project code. Then it's not necessary to distribute Pimlico itself
with the project – it will be downloaded by running this tool.
Another use is to get a whole new project up and running: `newproject.py` calls this script.

* `add_copyright.py`  
Tool for **updating the copyright statement** at the top of all Python code files and making sure that 
all files have it. It's a pain to make sure every file gets this and even more of a pain to change 
the text in all files. This can be run now and again to keep copyright statements in order 
throughout the codebase.