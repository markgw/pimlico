.. _example-pipeline-tokenize-example2:

tokenize\_example2
~~~~~~~~~~~~~~~~~~



This is an example Pimlico pipeline.

The complete config file for this example pipeline is below. `Source file <https://github.com/markgw/pimlico/blob/master/examples/simple/tokenize2.conf>`_

A simple example pipeline that loads some textual data and tokenizes it,
using an extremely simple tokenizer.

This is an example of a simple pipeline, but not a good example of how to
do tokenization.
For real applications, you should use a proper, language-specific tokenizer,
like the :mod:`OpenNLP one <pimlico.modules.opennlp.tokenize>`,
or at least :mod:`NLTK's NIST tokenizer <pimlico.modules.nltk.nist_tokenize>`.

Pipeline config
===============

.. code-block:: ini
   
   # Options for the whole pipeline
   [pipeline]
   name=tokenize_example2
   # Specify the version of Pimlico this config is designed to work with
   # It will run with any release that's the same major version and the same or a later minor version
   # Here we use "latest" so we're always running the example against the latest version,
   #  but you should specify the version you wrote the pipeline for
   release=latest
   # We need to load the input reader type, which is the same one used for the topic
   # modelling example
   python_path=../topic_modelling/src/
   
   # Specify some things in variables at the top of the file, so they're easy to find
   [vars]
   # The main pipeline input dir is given here
   # It's good to put all paths to input data here, so that it's easy for people to point
   #  them to other locations
   # Here we define where the example input text data can be found
   text_path=%(pimlico_root)s/examples/data/input/ubuntu_dialogue/dialogues_bigger.json
   
   # Read in the raw text from the JSON files
   [input_text]
   type=tm_example.modules.input.ubuntu_dialogue
   path=%(text_path)s
   
   # Tokenize the text using a very simple tokenizer
   # For real applications, you should use a proper, language-specific tokenizer,
   #  like the OpenNLP one, or at least NLTK's NIST tokenizer
   [tokenize]
   type=pimlico.modules.text.simple_tokenize
   input=input_text

Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.text.simple_tokenize`
    

