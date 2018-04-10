Models
======

This directory stores models for use by many different modules. For example, the OpenNLP modules require 
trained models, which can be downloaded from the OpenNLP website and will be looked for here.

In the future, Pimlico will contain tools for getting hold of model data directly, e.g. downloading 
from the website of the tool. For the time being, most models can be fetched using the `Makefile`. 

For example, to get hold of the default English parsing model for Malt, run `make malt` in this 
directory.
