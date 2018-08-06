# Temporary script to create and write out data to be used by unit tests
# Should be removed after use
import os

from pimlico import TEST_DATA_DIR
from pimlico.core.config import PipelineConfig
from pimlico.datatypes.dictionary import DictionaryData, Dictionary

output_base_dir = os.path.join(TEST_DATA_DIR, "datasets")
# Change this for different datatypes
output_dir = os.path.join(output_base_dir, "dictionary")

# Create an empty pipeline
pipeline = PipelineConfig.empty()

# Prepare data
data = DictionaryData()
data.add_documents([
    "here is some data".split(),
    "i'm adding some data to the dictionary".split(),
    "the dictionary includes several documents".split(),
    "the documents include several words".split(),
    "the words exhibit some overall between documents".split()
])

# Instantiate the datatype
datatype = Dictionary()

# Make a writer and write out data
with datatype.get_writer(output_dir, pipeline) as writer:
    writer.data