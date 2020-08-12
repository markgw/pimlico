.. _example-pipeline-train-tms-example:

train\_tms\_example
~~~~~~~~~~~~~~~~~~~



This is an example Pimlico pipeline.

The complete config file for this example pipeline is below. `Source file <https://github.com/markgw/pimlico/blob/master/examples/topic_modelling/train_tms.conf>`_

An example pipeline that loads some textual data and trains topic
models on it using Gensim.

See the ``src/`` subdirectory for the module's code.

Pipeline config
===============

.. code-block:: ini
   
   [pipeline]
   name=train_tms_example
   release=latest
   # We need a path to Python code here, since we use a custom module type
   python_path=src/
   
   [vars]
   # Here we define where the example input corpus can be found
   corpus_path=%(pimlico_root)s/examples/data/input/ubuntu_dialogue/dialogues_small.json
   
   # Read in the raw text from the JSON files
   [input_text]
   type=tm_example.modules.input.ubuntu_dialogue
   path=%(corpus_path)s
   # Just use a small number of documents so we can train fast
   # You should use a much bigger corpus for a real model
   limit=600
   
   # Also read in a label for each document consisting of the year+month from
   # the timestamp
   [input_labels]
   type=tm_example.modules.input.ubuntu_dialogue_months
   path=%(corpus_path)s
   limit=600
   
   [store_labels]
   type=pimlico.modules.corpora.store
   input=input_labels
   
   # Tokenize the text using a simple tokenizer from NLTK
   [tokenize]
   type=pimlico.modules.spacy.tokenize
   input=input_text
   
   # Apply simple text normalization
   # In a real topic modelling application, you might want to do lemmatization
   #  or other types of more sophisticated normalization here
   [normalize]
   type=pimlico.modules.text.normalize
   case=lower
   min_word_length=3
   remove_empty=T
   remove_only_punct=T
   
   # Build a vocabulary from the words used in the corpus
   # This is used to map words in the corpus to IDs
   [vocab]
   type=pimlico.modules.corpora.vocab_builder
   input=normalize
   # Only include words that occur at least 5 times
   threshold=5
   
   [ids]
   type=pimlico.modules.corpora.vocab_mapper
   input_vocab=vocab
   input_text=normalize
   # Skip any OOV words (below the threshold)
   oov=ignore
   
   # First train a plain LDA model using Gensim
   [lda]
   type=pimlico.modules.gensim.lda
   input_vocab=vocab
   input_corpus=ids
   tfidf=T
   # Small number of topics: you probably want more in practice
   num_topics=5
   passes=10
   
   # Also train a dynamic topic model (DTM), with a separate model
   # for each month
   [dtm]
   type=pimlico.modules.gensim.ldaseq
   input_corpus=ids
   input_labels=input_labels
   input_vocab=vocab
   # Small number of topics: you probably want more in practice
   num_topics=5
   # Apply TF-IDF transformation to bags of words before training
   tfidf=T
   # Speed up training for this demo by reducing iterations
   em_min_iter=3
   em_max_iter=8
   
   # Apply stationary DTM inference to all of the documents
   # This doesn't need to be run on the same document set we trained on:
   #  we do that here just as an example
   [dtm_infer]
   type=pimlico.modules.gensim.ldaseq_doc_topics
   input_corpus=ids
   input_labels=input_labels
   input_model=dtm

Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.store`
 * :mod:`pimlico.modules.spacy.tokenize`
 * :mod:`pimlico.modules.text.normalize`
 * :mod:`pimlico.modules.corpora.vocab_builder`
 * :mod:`pimlico.modules.corpora.vocab_mapper`
 * :mod:`pimlico.modules.gensim.lda`
 * :mod:`pimlico.modules.gensim.ldaseq`
 * :mod:`pimlico.modules.gensim.ldaseq_doc_topics`
    

