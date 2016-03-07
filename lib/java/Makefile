OS := $(shell uname)
ifeq ($(OS), Darwin)
	# Mac
	FETCH := curl -L -O
	FETCH_STDOUT := curl -L
else
	# Linux, etc
	FETCH := wget
	FETCH_STDOUT := wget -O -
endif


all :
	$(MAKE) opennlp
	$(MAKE) stanford-parser
	$(MAKE) guava.jar
	$(MAKE) stanford-tagger
	$(MAKE) argparse4j.jar

########## OPEN NLP ##############
opennlp : opennlp-maxent-3.0.3.jar opennlp-tools-1.5.3.jar opennlp-uima-1.5.3.jar jwnl-1.3.3.jar
	# Clear up downloaded archive
	rm -f apache-opennlp-1.5.3-bin.tar.gz

opennlp-maxent-3.0.3.jar : 
	$(MAKE) apache-opennlp-1.5.3-bin.tar.gz
	tar xzf apache-opennlp-1.5.3-bin.tar.gz apache-opennlp-1.5.3/lib/opennlp-maxent-3.0.3.jar
	mv apache-opennlp-1.5.3/lib/opennlp-maxent-3.0.3.jar .
	rm -rf apache-opennlp-1.5.3
opennlp-tools-1.5.3.jar : 
	$(MAKE) apache-opennlp-1.5.3-bin.tar.gz
	tar xzf apache-opennlp-1.5.3-bin.tar.gz apache-opennlp-1.5.3/lib/opennlp-tools-1.5.3.jar
	mv apache-opennlp-1.5.3/lib/opennlp-tools-1.5.3.jar .
	rm -rf apache-opennlp-1.5.3
opennlp-uima-1.5.3.jar : 
	$(MAKE) apache-opennlp-1.5.3-bin.tar.gz
	tar xzf apache-opennlp-1.5.3-bin.tar.gz apache-opennlp-1.5.3/lib/opennlp-uima-1.5.3.jar
	mv apache-opennlp-1.5.3/lib/opennlp-uima-1.5.3.jar .
	rm -rf apache-opennlp-1.5.3
src/opennlp :
	$(FETCH) http://apache.mirror.anlx.net//opennlp/opennlp-1.5.3/apache-opennlp-1.5.3-src.tar.gz
	tar xzf apache-opennlp-1.5.3-src.tar.gz apache-opennlp-1.5.3-src
	mkdir -p src
	mv apache-opennlp-1.5.3-src src/opennlp
	rm apache-opennlp-1.5.3-src.tar.gz
jwnl-1.3.3.jar : 
	$(MAKE) apache-opennlp-1.5.3-bin.tar.gz
	tar xzf apache-opennlp-1.5.3-bin.tar.gz apache-opennlp-1.5.3/lib/jwnl-1.3.3.jar
	mv apache-opennlp-1.5.3/lib/jwnl-1.3.3.jar .
	rm -rf apache-opennlp-1.5.3

apache-opennlp-1.5.3-bin.tar.gz :
	# Fetch OpenNlp archive
	$(FETCH) http://apache.mesi.com.ar//opennlp/opennlp-1.5.3/apache-opennlp-1.5.3-bin.tar.gz

argparse4j.jar :
	$(FETCH_STDOUT) http://sourceforge.net/projects/argparse4j/files/latest/download?source=files >argparse4j.jar

###################################
	
stanford-parser :
	$(MAKE) stanford-parser-full-2014-01-04.zip
	unzip stanford-parser-full-2014-01-04.zip
	mv stanford-parser-full-2014-01-04/ stanford-parser
	rm stanford-parser-full-2014-01-04.zip

stanford-parser-full-2014-01-04.zip :
	$(FETCH) http://nlp.stanford.edu/software/stanford-parser-full-2014-01-04.zip

stanford-tagger : 
	$(MAKE) stanford-postagger-2014-01-04.zip
	unzip stanford-postagger-2014-01-04.zip
	mv stanford-postagger-2014-01-04 stanford-tagger
	rm stanford-postagger-2014-01-04.zip

stanford-postagger-2014-01-04.zip :
	$(FETCH) http://nlp.stanford.edu/downloads/stanford-postagger-2014-01-04.zip
	
####################################

guava.jar :
	@echo "Fetching Guava"
	$(FETCH_STDOUT) http://search.maven.org/remotecontent?filepath=com/google/guava/guava/15.0/guava-15.0.jar >guava.jar

malt : maltparser-1.8.1.jar

maltparser-1.8.1.jar : log4j-1.2.17.jar liblinear-java-1.95.jar
	$(FETCH) http://maltparser.org/dist/maltparser-1.8.1.tar.gz
	tar -xzf maltparser-1.8.1.tar.gz maltparser-1.8.1/maltparser-1.8.1.jar
	mv maltparser-1.8.1/maltparser-1.8.1.jar .
	rmdir maltparser-1.8.1
	rm maltparser-1.8.1.tar.gz
