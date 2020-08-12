# Ubuntu Dialogue Corpus

A small sample from the [Ubuntu Dialogue Corpus](https://www.kaggle.com/rtatman/ubuntu-dialogue-corpus/data). 

## Subsample

The sample has been chosen by loading all conversations with their 
timestamps from the corpus and subsampling 20 conversations per month. 
The corpus covers 101 months.

See the Python scripts in this directory for how the subsample was 
generated.

## Purpose

The dataset is used in the topic modelling example pipeline.

In particular, it has timestamps, so can be used to train a 
Dynamic Topic Model.

## How to use

Take a look at the topic modelling example pipeline to see how we 
use a custom input reader to read in the corpus.

## License

The original dataset is licensed under the Apache License v2.0. This 
subset maintains the same license.
