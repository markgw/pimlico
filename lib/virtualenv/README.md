Virtualenvs
===========

This directory is used to store Python virtualenvs for running Pimlico, created automatically as 
necessary by Pimlico.

If no custom virtualenv is requested, the default, called `default`, is used. Otherwise, another name may be
specified using the `PIMENV` environment variable.

A virtualenv will be created automatically when Pimlico is run. All Python software required by the Pimlico
pipeline will be installed there.
