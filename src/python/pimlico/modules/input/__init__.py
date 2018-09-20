"""
Input readers

Various input readers for various datatypes. These are used to read in data from some external source,
such as a corpus in its distributed format (e.g. XML files or a collection of text files), and present
it to the Pimlico pipeline as a Pimlico dataset, which can be used as input to other modules.

They do not typically store the data as a Pimlico dataset, but produce it on the fly, although sometimes
it could be appropriate to do otherwise.

Note that there can be multiple input readers for a single datatype. For example, there are many ways
to read in a corpus of raw text documents, depending on the format they're stored in. They might
by in one big XML file, text files collected into compressed archives, a big text file with document
separators, etc. These all require their own input reader and all of them produce the same output
corpus type.

"""
