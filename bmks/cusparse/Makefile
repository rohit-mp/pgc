include ../common.mk

include app.mk

# do not change anything below unless you know what you're doing
DSTDIR=$(GENSRC)/$(BMKNAME)

all: $(DSTDIR) $(BMKNAME)

$(BMKNAME): $(DSTDIR)/Makefile $(DSTDIR)/kernel.cu $(DSTDIR)/bmktest2.py 

$(DSTDIR)/Makefile: GENMakefile
	ln -sf ../../bmks/$(BMKNAME)/$< $@

$(DSTDIR)/kernel.cu: $(SRCPY)
	ln -sf ../../bmks/$(BMKNAME)/$< $@

include ../common-rules.mk

$(DSTDIR)/bmktest2.py: 
	ln -sf ../../bmks/$(BMKNAME)/bmktest2.py $@ 
