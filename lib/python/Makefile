# This makefile serves to fetch dependencies as you need them
# Just cd to the directory containing the Makefile (lib/python) and type:
#  make dependency-name
# to fetch a particular dependency.
#
# The target "core" fetches all the dependencies needed for the core of Pimlico, which
# you'll almost certainly need, no matter what tools you're using:
#  make core

OS := $(shell uname)
ifeq ($(OS), Darwin)
	# Mac
	# -L makes curl follow redirects
	FETCH := curl -L -O
	FETCH_STDOUT := curl -L
else
	# Linux, etc
	FETCH := wget
	FETCH_STDOUT := wget -O -
endif

###############
# Basic dependencies of core parts of Pimlico
core :
	$(MAKE) progressbar
	$(MAKE) tabulate.py

tabulate.py :
	$(FETCH) https://pypi.python.org/packages/source/t/tabulate/tabulate-0.7.3.tar.gz
	tar -xzf tabulate-0.7.3.tar.gz tabulate-0.7.3/tabulate.py
	mv tabulate-0.7.3/tabulate.py .
	rmdir tabulate-0.7.3

###############
gensim :
	$(FETCH) https://pypi.python.org/packages/source/g/gensim/gensim-0.12.3.tar.gz
	tar -zxf gensim-0.12.3.tar.gz gensim-0.12.3/gensim
	mv gensim-0.12.3/gensim . && rm gensim-0.12.3.tar.gz
	rm -rf gensim-0.12.3
