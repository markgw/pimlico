# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Datatypes for storing and loading Keras models.

"""
from __future__ import absolute_import

import json
import os
from pimlico.core.dependencies.python import keras_dependency
from pimlico.datatypes import PimlicoDatatype
from pimlico.datatypes.base import DatatypeWriteError

from pimlico.utils.core import import_member


class KerasModel(PimlicoDatatype):
    """
    Datatype for both types of Keras models, stored using Keras' own storage mechanisms.
    This uses Keras' method of storing the model architecture as JSON and stores the weights using hdf5.

    """
    datatype_name = "keras_model"
    # Override to pass in extra values in Keras' custom objects arg to model_from_json
    # May be given as string fully-qualified Python names
    custom_objects = {}
    datatype_supports_python2 = True

    def get_software_dependencies(self):
        return super(KerasModel, self).get_software_dependencies() + [keras_dependency]

    class Reader(object):
        def get_custom_objects(self):
            new_co = {}
            for name, cls in self.datatype.custom_objects.iteritems():
                if isinstance(cls, basestring):
                    # Import the class
                    cls = import_member(cls)
                new_co[name] = cls
            return new_co

        def load_model(self):
            from keras.models import model_from_json
            # Load the model architecture
            with open(os.path.join(self.data_dir, "architecture.json"), "r") as arch_file:
                model = model_from_json(arch_file.read(), custom_objects=self.get_custom_objects())
            # Set the weights to those stored
            model.load_weights(os.path.join(self.data_dir, "weights.hdf5"))
            return model

    class Writer(object):
        required_tasks = ["architecture", "weights"]

        @property
        def weights_filename(self):
            return os.path.join(self.data_dir, "weights.hdf5")

        def write_model(self, model):
            self.write_architecture(model)
            self.write_weights(model)

        def write_architecture(self, model):
            # Store the model's architecture
            with open(os.path.join(self.data_dir, "architecture.json"), "w") as arch_file:
                arch_file.write(model.to_json())
            self.task_complete("architecture")

        def write_weights(self, model):
            # Store the model's weights
            model.save_weights(self.weights_filename, overwrite=True)
            self.task_complete("weights")


class KerasModelBuilderClass(PimlicoDatatype):
    """
    An alternative way to store Keras models.

    Create a class whose init method build the model architecture. It should take a kwarg called `build_params`,
    which is a JSON-encodable dictionary of parameters that determine how the model gets build (hyperparameters).
    When you initialize your model for training, create this hyperparameter dictionary and use it to instantiate
    the model class.

    Use the KerasModelBuilderClassWriter to store the model during training.
    Create a writer, then start model training, storing the weights to the filename given by the `weights_filename`
    attribute of the writer. The hyperparameter dictionary will also be stored.

    The writer also stores the fully-qualified path of the model-builder class. When we read the datatype
    and want to rebuild the model, we import the class, instantiate it and then set its weights to those we've
    stored.

    The model builder class must have the model stored in an attribute `model`.

    """
    datatype_name = "keras_model_builder_class"
    datatype_supports_python2 = True

    class Reader(object):
        @property
        def weights_filename(self):
            if self.data_dir is not None:
                return os.path.join(self.data_dir, "weights.hdf5")

        def load_build_params(self):
            with open(os.path.join(self.data_dir, "build_params.json"), "r") as f:
                return json.load(f)

        def create_builder_class(self, override_params=None):
            params = self.load_build_params()
            builder_class_path = params.pop("builder_class_path")
            # Allow some params to be overridden at load time, so they're not the same ones the model was trained with
            if override_params is not None:
                params.update(override_params)
            # Try to import the class that builds the model
            cls = import_member(builder_class_path)
            # Instantiate the builder class with the build params
            model_builder = cls(build_params=params)
            return model_builder

        def load_model(self, override_params=None):
            """
            Instantiate the model builder class with the stored parameters and set the weights on the model to those
            stored.

            :return: model builder instance (keras model in attribute `model`
            """
            builder = self.create_builder_class(override_params=override_params)
            # Set the stored parameters
            builder.model.load_weights(self.weights_filename)
            return builder

    class Writer(object):
        required_tasks = ["architecture", "weights"]

        def __init__(self, *args, **kwargs):
            build_params = kwargs.pop("build_params", {})
            if "builder_class_path" not in kwargs:
                raise DatatypeWriteError("builder_class_path must be supplied for a Keras model builder class writer")
            build_params["builder_class_path"] = kwargs.pop("builder_class_path")

            super(KerasModelBuilderClass.Writer, self).__init__(*args, **kwargs)
            self.weights_filename = os.path.join(self.data_dir, "weights.hdf5")
            self.build_params = build_params

        def __enter__(self):
            super(KerasModelBuilderClass.Writer, self).__enter__()
            # Store the model-building hyperparameters as JSON
            with open(os.path.join(self.data_dir, "build_params.json"), "w") as f:
                json.dump(self.build_params, f, indent=4)
            self.task_complete("architecture")
            return self

        def write_weights(self, model):
            # Store the model's weights
            model.save_weights(self.weights_filename, overwrite=True)
            self.task_complete("weights")
