OS := $(shell uname)
ifeq ($(OS), Darwin)
	# Mac
	FETCH := curl -O
else
	# Linux, etc
	FETCH := wget
endif


########## OPEN NLP ##############
opennlp : opennlp/en-sent.bin opennlp/en-token.bin opennlp/en-pos-maxent.bin opennlp/en-parser-chunking.bin opennlp-coref

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

opennlp-coref :
	# All coref models
	mkdir -p opennlp
	cd opennlp && for filename in acronyms cmodel.bin.gz cmodel.events cmodel.nr.bin.gz defmodel.bin.gz defmodel.events defmodel.nr.bin.gz fmodel.bin.gz fmodel.events fmodel.nr.bin.gz gen.bin.gz gen.events gen.fem gen.mas imodel.bin.gz imodel.events imodel.nr.bin.gz num.bin.gz plmodel.bin.gz plmodel.events plmodel.nr.bin.gz pmodel.bin.gz pmodel.events pmodel.nr.bin.gz pnmodel.bin.gz pnmodel.events pnmodel.nr.bin.gz sim.bin.gz tmodel.bin.gz tmodel.events tmodel.nr.bin.gz; do $(FETCH) http://opennlp.sourceforge.net/models-1.4/english/coref/$$filename; done

###################################
