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

progressbar :
	$(FETCH_STDOUT) https://github.com/WoLpH/python-progressbar/archive/v2.6.2.tar.gz >progressbar.tar.gz
	tar xzf progressbar.tar.gz python-progressbar-2.6.2/progressbar
	mv python-progressbar-2.6.2/progressbar .
	rm -rf progressbar.tar.gz python-progressbar-2.6.2

###############
py4j :
	$(FETCH) https://pypi.python.org/packages/source/p/py4j/py4j-0.9.2.tar.gz
	tar -xzf py4j-0.9.2.tar.gz py4j-0.9.2/src/py4j
	mv py4j-0.9.2/src/py4j . && rm -r py4j-0.9.2 && rm py4j-0.9.2.tar.gz

gensim :
	$(FETCH) https://pypi.python.org/packages/source/g/gensim/gensim-0.12.3.tar.gz
	tar -zxf gensim-0.12.3.tar.gz gensim-0.12.3/gensim
	mv gensim-0.12.3/gensim . && rm gensim-0.12.3.tar.gz
	rm -rf gensim-0.12.3

bs4 :
	$(FETCH) http://www.crummy.com/software/BeautifulSoup/bs4/download/4.3/beautifulsoup4-4.3.2.tar.gz
	tar -xzf beautifulsoup4-4.3.2.tar.gz beautifulsoup4-4.3.2/bs4/
	mv beautifulsoup4-4.3.2/bs4 .
	rmdir beautifulsoup4-4.3.2
	rm beautifulsoup4-4.3.2.tar.gz

################
stanford : requests

requests :
	$(FETCH) https://github.com/kennethreitz/requests/archive/master.zip
	unzip master.zip
	mv requests-master/requests .
	rm -rf requests-master/ master.zip

################
urwid:
	$(FETCH) https://pypi.python.org/packages/source/u/urwid/urwid-1.3.1.tar.gz
	tar xzf urwid-1.3.1.tar.gz urwid-1.3.1/urwid
	rm urwid-1.3.1.tar.gz
	mv urwid-1.3.1/urwid .
	rmdir urwid-1.3.1
