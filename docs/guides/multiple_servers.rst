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