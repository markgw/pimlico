"""
Datatypes for storing and loading Keras models.

"""
from __future__ import absolute_import
import os
from pimlico.core.dependencies.python import keras_dependency

from pimlico.datatypes.base import PimlicoDatatypeWriter, PimlicoDatatype
from pimlico.utils.core import import_member


class KerasModelWriter(PimlicoDatatypeWriter):
    """
    Writer for storing both types of Keras model (since they provide the same storage interface).

    """
    def __init__(self, base_dir, **kwargs):
        super(KerasModelWriter, self).__init__(base_dir, **kwargs)
        self.require_tasks("architecture", "weights")

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
        model.save_weights(os.path.join(self.data_dir, "weights.hdf5"), overwrite=True)
        self.task_complete("weights")


class KerasModel(PimlicoDatatype):
    """
    Datatype for both types of Keras models, stored using Keras' own storage mechanisms.

    """
    # Override to pass in extra values in Keras' custom objects arg to model_from_json
    # May be given as string fully-qualified Python names
    custom_objects = {}

    def get_software_dependencies(self):
        return super(KerasModel, self).get_software_dependencies() + [keras_dependency]
    
    def get_custom_objects(self):
        new_co = {}
        for name, cls in self.custom_objects.iteritems():
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
