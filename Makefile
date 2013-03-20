# Makefile that calls setup.py with the arguments passed to make.
# Included as a convenience for using the :make command in vim
#
# To stop make from handling arguments like --help, use --:
# $ make -- test --help

-include Makefile.local

MAKEFLAGS=-s

ifeq ($(MAKECMDGOALS),)
MAKECMDGOALS=test
endif

.SUFFIXES:
.PHONY: $(MAKECMDGOALS) .all

$(MAKECMDGOALS): .all

.all:
	./setup.py $(MAKECMDGOALS)
