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


########## Meta targets ##########
# These are collections of targets for whole modules, including all the dependencies for the module
opennlp : opennlp-all py4j argparse4j guava


########## OPEN NLP ##############
opennlp-all : opennlp-maxent-3.0.3.jar opennlp-tools-1.5.3.jar opennlp-uima-1.5.3.jar jwnl-1.3.3.jar
	# Clear up downloaded archive
	rm -f apache-opennlp-1.5.3-bin.tar.gz
	$(MAKE) argparse4j.jar

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
jwnl-1.3.3.jar : 
	$(MAKE) apache-opennlp-1.5.3-bin.tar.gz
	tar xzf apache-opennlp-1.5.3-bin.tar.gz apache-opennlp-1.5.3/lib/jwnl-1.3.3.jar
	mv apache-opennlp-1.5.3/lib/jwnl-1.3.3.jar .
	rm -rf apache-opennlp-1.5.3

apache-opennlp-1.5.3-bin.tar.gz :
	# Fetch OpenNlp archive
	$(FETCH) http://apache.mesi.com.ar//opennlp/opennlp-1.5.3/apache-opennlp-1.5.3-bin.tar.gz

# Optionally, also fetch OpenNLP src files, useful for debugging wrappers, etc
opennlp-src : src/opennlp
src/opennlp :
	$(FETCH) http://apache.mirror.anlx.net//opennlp/opennlp-1.5.3/apache-opennlp-1.5.3-src.tar.gz
	tar xzf apache-opennlp-1.5.3-src.tar.gz apache-opennlp-1.5.3-src
	mkdir -p src
	mv apache-opennlp-1.5.3-src src/opennlp
	rm apache-opennlp-1.5.3-src.tar.gz

##############################

argparse4j : argparse4j.jar

argparse4j.jar :
	$(FETCH_STDOUT) http://sourceforge.net/projects/argparse4j/files/latest/download?source=files >argparse4j.jar

########## Py4j ##############
py4j : py4j0.9.2.jar

py4j0.9.2.jar :
	$(FETCH) https://pypi.python.org/packages/source/p/py4j/py4j-0.9.2.tar.gz
	tar -zxf py4j-0.9.2.tar.gz py4j-0.9.2/py4j-java/py4j0.9.2.jar
	mv py4j-0.9.2/py4j-java/py4j0.9.2.jar . && rm -r py4j-0.9.2/
	rm py4j-0.9.2.tar.gz

###################################
	
corenlp : stanford-corenlp-3.6.0.jar

stanford-corenlp-3.6.0.jar :
	$(FETCH) http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip
	unzip stanford-corenlp-full-2015-12-09.zip
	mv stanford-corenlp-full-2015-12-09/*.jar .
	rm -rf stanford-corenlp-full-2015-12-09 stanford-corenlp-full-2015-12-09.zip

##################################

guava : guava.jar

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

log4j-1.2.17.jar :
	$(FETCH) http://www.us.apache.org/dist/logging/log4j/1.2.17/log4j-1.2.17.tar.gz
	tar -xzf log4j-1.2.17.tar.gz apache-log4j-1.2.17/log4j-1.2.17.jar
	mv apache-log4j-1.2.17/log4j-1.2.17.jar .
	rmdir apache-log4j-1.2.17
	rm log4j-1.2.17.tar.gz

liblinear-java-1.95.jar :
	$(FETCH) http://www.bwaldvogel.de/liblinear-java/liblinear-java-1.95.jar

############ Caevo ############

caevo : caevo-1.1.jar
caevo-1.1.jar :
	# Check we've got Maven
	@if ! mvn -v >/dev/null; then echo "Caevo build requires Maven: please install"; exit 1; fi
	$(MAKE) src/caevo
	# Get hold of the WordNet dictionaries
	if [ !-d src/caevo/src/test/resources/wordnet/dict ]; then cd src/caevo && ./download-wordnet-dictionaries; fi
	# Build Caevo using Maven
	cd src/caevo && mvn compile
	# Package Caevo up, together with dependencies, in jar
	cd src/caevo && JWNL=src/test/resources/jwnl_file_properties.xml mvn package assembly:single
	# Put the jars in the lib dir, where Pimlico can find it
	mv src/caevo/target/caevo-1.1-jar-with-dependencies.jar .
	mv src/caevo/target/caevo-1.1.jar .
	# Put sieve configs in models dir
	mkdir -p ../../models/caevo
	cp src/caevo/*.sieves ../../models/caevo/
	# And wordnet files
	if [ ! -d ../../models/caevo/dict ]; then cp -r src/caevo/src/test/resources/wordnet/dict ../../models/caevo; fi
	# Keep the source code for debugging purposes for now

src/caevo :
	# Fetch Caevo code
	$(FETCH_STDOUT) https://github.com/nchambers/caevo/archive/8cfc810baff833063da9b423ef7a36983b3ab0e2.zip >caevo.zip
	unzip caevo.zip
	mkdir -p src
	mv caevo-8cfc810baff833063da9b423ef7a36983b3ab0e2 src/caevo
	rm caevo.zip


############ C&C parser, Java version #######
candc.jar :
	$(FETCH) https://www.cl.cam.ac.uk/~sc609/java-candc/java-candc-v0.95.tgz
	mkdir -p candc
	cd candc && mv ../java-candc-v0.95.tgz . && tar xzf java-candc-v0.95.tgz
	rm candc/java-candc-v0.95.tgz
	cd candc && ./compile
	# Put the built classes in a Jar file
	cd candc/bin && jar cf candc.jar *
	mv candc/bin/candc.jar .
	# Leave the unpacked archive here so we can find the models, grammar, etc
