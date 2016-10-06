OS := $(shell uname)
ifeq ($(OS), Darwin)
	# Mac
	FETCH := curl -O
else
	# Linux, etc
	FETCH := wget
endif


.PHONY : malt


########## OPEN NLP ##############
opennlp : opennlp/en-sent.bin opennlp/en-token.bin opennlp/en-pos-maxent.bin opennlp/en-parser-chunking.bin opennlp-coref opennlp/en-ner-person.bin

opennlp/en-sent.bin :
	# OpenNLP English sentence detection model
	mkdir -p opennlp
	cd opennlp && $(FETCH) http://opennlp.sourceforge.net/models-1.5/en-sent.bin

opennlp/en-token.bin :
	# OpenNLP English tokenization model
	mkdir -p opennlp
	cd opennlp && $(FETCH) http://opennlp.sourceforge.net/models-1.5/en-token.bin

opennlp/en-pos-maxent.bin :
	# OpenNLP English POS tagging model
	mkdir -p opennlp
	cd opennlp && $(FETCH) http://opennlp.sourceforge.net/models-1.5/en-pos-maxent.bin

opennlp/en-parser-chunking.bin :
	# OpenNLP English chunking parser model
	mkdir -p opennlp
	cd opennlp && $(FETCH) http://opennlp.sourceforge.net/models-1.5/en-parser-chunking.bin

opennlp/en-ner-person.bin :
	# OpenNLP English person name finder model
	mkdir -p opennlp
	cd opennlp && $(FETCH) http://opennlp.sourceforge.net/models-1.5/en-ner-person.bin

opennlp-coref : wordnet/db-3.1
	# All coref models
	mkdir -p opennlp
	cd opennlp && for filename in acronyms cmodel.bin.gz cmodel.events cmodel.nr.bin.gz defmodel.bin.gz defmodel.events defmodel.nr.bin.gz fmodel.bin.gz fmodel.events fmodel.nr.bin.gz gen.bin.gz gen.events gen.fem gen.mas imodel.bin.gz imodel.events imodel.nr.bin.gz num.bin.gz plmodel.bin.gz plmodel.events plmodel.nr.bin.gz pmodel.bin.gz pmodel.events pmodel.nr.bin.gz pnmodel.bin.gz pnmodel.events pnmodel.nr.bin.gz sim.bin.gz tmodel.bin.gz tmodel.events tmodel.nr.bin.gz; do $(FETCH) http://opennlp.sourceforge.net/models-1.4/english/coref/$$filename; done

###################################
# WordNet dictionary files (full WN database), without source code
wordnet/db-3.1 :
	mkdir -p wordnet
	$(FETCH) http://wordnetcode.princeton.edu/wn3.1.dict.tar.gz
	tar -zxf wn3.1.dict.tar.gz
	mv dict/ wordnet/db-3.1
	rm -rf wn3.1.dict.tar.gz

######### Malt parser ############
# Default Malt parser model
malt : malt/engmalt.linear-1.7.mco
malt/engmalt.linear-1.7.mco :
	mkdir -p malt
	cd malt && $(FETCH) http://www.maltparser.org/mco/english_parser/engmalt.linear-1.7.mco
