============================
Outputting pipeline diagrams
============================

Once pipeline config files get big, it can be difficult to follow what's going on in them, especially if the
structure is more complex than just a linear pipeline. A useful feature would be the ability to display/output
a visualization of the pipeline as a flow graph.

It looks like the easiest way to do this will be to construct a DOT graph using Graphviz/Pydot and then
output the diagram using Graphviz.

http://www.graphviz.org

https://pypi.python.org/pypi/pydot

Building the graph should be pretty straightforward, since the mapping from modules to nodes is fairly direct.

We could also add extra information to the nodes, like current execution status.
