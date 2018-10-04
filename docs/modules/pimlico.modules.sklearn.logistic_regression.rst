Sklearn logistic regression
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.sklearn.logistic_regression

+------------+---------------------------------------------+
| Path       | pimlico.modules.sklearn.logistic_regression |
+------------+---------------------------------------------+
| Executable | yes                                         |
+------------+---------------------------------------------+

Provides an interface to `Scikit-Learn's <http://scikit-learn.org/stable/>`_ simple
`logistic regression <scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html>`_
trainer.

You may also want to consider using:

 - `LogisticRegressionCV <scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegressionCV.html>`_:
   LR with cross-validation to choose regularization strength

 - `SGDClassifier <scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html>`_:
   general gradient-descent training for classifiers, which includes logistic regression.
   A better choice for training on a large dataset.


Inputs
======

+----------+--------------------------------------------------------------------------------------+
| Name     | Type(s)                                                                              |
+==========+======================================================================================+
| features | :class:`scored_real_feature_sets <pimlico.datatypes.features.ScoredRealFeatureSets>` |
+----------+--------------------------------------------------------------------------------------+

Outputs
=======

+-------+-----------------------------------------------------------------+
| Name  | Type(s)                                                         |
+=======+=================================================================+
| model | :class:`sklearn_model <pimlico.datatypes.sklearn.SklearnModel>` |
+-------+-----------------------------------------------------------------+

Options
=======

+---------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+
| Name    | Description                                                                                                                                               | Type      |
+=========+===========================================================================================================================================================+===========+
| options | Options to pass into the constructor of LogisticRegression, formatted as a JSON dictionary (potentially without the {}s). E.g.: '"C":1.5, "penalty":"l2"' | JSON dict |
+---------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_sklearn_log_reg_module]
   type=pimlico.modules.sklearn.logistic_regression
   input_features=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_sklearn_log_reg_module]
   type=pimlico.modules.sklearn.logistic_regression
   input_features=module_a.some_output
   options="C":1.5, "penalty":"l2"

