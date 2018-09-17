!! Sklearn matrix factorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.sklearn.matrix_factorization

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+----------------------------------------------+
| Path       | pimlico.modules.sklearn.matrix_factorization |
+------------+----------------------------------------------+
| Executable | yes                                          |
+------------+----------------------------------------------+

Provides a simple interface to `Scikit-Learn's <http://scikit-learn.org/stable/>`_ various matrix factorization
models.

Since they provide a consistent training interface, you can simply choose the class name of the method you
want to use and specify options relevant to that method in the ``options`` option. For available options,
take a look at the table of parameters in the
`Scikit-Learn documentation <http://scikit-learn.org/stable/modules/classes.html#module-sklearn.decomposition>`_
for each class.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| matrix | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+------+---------------------------------------+
| Name | Type(s)                               |
+======+=======================================+
| w    | **invalid output type specification** |
+------+---------------------------------------+
| h    | **invalid output type specification** |
+------+---------------------------------------+

Options
=======

+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Name    | Description                                                                                                                                                                                                                                                                                                                                            | Type                                                                                                                                           |
+=========+========================================================================================================================================================================================================================================================================================================================================================+================================================================================================================================================+
| class   | (required) Scikit-learn class to use to fit the matrix factorization. Should be the name of a class in the package sklearn.decomposition that has a fit_transform() method and a components\_ attribute. Supported classes: NMF, SparsePCA, ProjectedGradientNMF, FastICA, FactorAnalysis, PCA, RandomizedPCA, LatentDirichletAllocation, TruncatedSVD | 'NMF', 'SparsePCA', 'ProjectedGradientNMF', 'FastICA', 'FactorAnalysis', 'PCA', 'RandomizedPCA', 'LatentDirichletAllocation' or 'TruncatedSVD' |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| options | Options to pass into the constructor of the sklearn class, formatted as a JSON dictionary (potentially without the {}s). E.g.: 'n_components=200, solver="cd", tol=0.0001, max_iter=200'                                                                                                                                                               | string                                                                                                                                         |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_sklearn_mat_fac_module]
   input_matrix=module_a.some_output
   class=value

This example usage includes more options.

.. code-block:: ini
   
   [my_sklearn_mat_fac_module]
   input_matrix=module_a.some_output
   class=value
   options=value

