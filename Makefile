#############################################################################
#
# Generic Makefile for C/C++ Program
#
# License: GPL (General Public License)
# Copyright (C) 2006-2007 by whyglinux <whyglinux AT gmail DOT com>
# Copyright (C) 2013 by CJP
#
# Description:
# ------------
# This is an easily customizable makefile template. The purpose is to
# provide an instant building environment for C/C++ programs.
#
# It searches all the C/C++ source files in the specified directories,
# makes dependencies, compiles and links to form an executable.
#
# Basically it can be used to build in the current working directory a
# C/C++ program in which only standard C/C++ libraries are concerned.
#
# Besides, you can easily customize it in the following ways:
#   * specify your favorite program name <PROGRAM>
#   * search sources in more directories <SRCDIRS>
#   * to use non-standard libraries, set <MY_CFLAGS> and <MY_LIBS>
#
# Once customized for a program, without any changes the makefile
# could then be used by all the same kind of programs to build them,
# even when source files are renamed, added or removed.
#
# The makefile is expected to be used with GNU make. Other versions
# of makes may possibly work but not tested.
#
# Usage:
# ------
# Just copy the makefile to your program directory and customize it.
#
# If nothing needs to be changed you can just make a symbolic link to
# the makefile instead, or use `make -f` to select the makefile
# directly when you do not want to make a copy or link.
#
# To build, install or distribute your program, the following make
# targets are available:
#
#   $ make           compile and link.
#   $ make NODEP=yes compile and link without generating dependencies.
#   $ make objs      compile only (no linking.)
#   $ make tags      create tags for Emacs.
#   $ make ctags     create ctags for VI.
#   $ make clean     clean objects and the executable file.
#   $ make distclean clean objects, the executable and dependencies.
#   $ make help      get the usage of the makefile.
#
#===========================================================================

## Customizable Section: adapt those variables to suit your program.
##==========================================================================

# The pre-processor and compiler options.
MY_CFLAGS = -I. -I/usr/include/uriparser

# The linker options.
MY_LIBS   = -lm -luriparser -lssl

# The pre-processor options used by the cpp (man cpp for more).
CPPFLAGS  = -Wall

# The options used in linking as well as in any direct use of ld.
LDFLAGS   =

# The directories in which source files reside.
# If not specified, only the current directory will be serached.
SRCDIRS   =

# The executable file name.
# If not specified, current directory name or `a.out' will be used.
PROGRAM   = amikopay
TEST_PROGRAM = test/test

#Add amiko pay to the source directories:
SRCDIRS = .
TEST_SRCDIRS = test

## Implicit Section: change the following only when necessary.
##==========================================================================

# The source file types (headers excluded).
# .c indicates C source files, and others C++ ones.
SRCEXTS = .c .C .cc .cpp .CPP .c++ .cxx .cp

# The header file types.
HDREXTS = .h .H .hh .hpp .HPP .h++ .hxx .hp

# The pre-processor and compiler options.
# Users can override those variables from the command line.
CFLAGS  = -O0
CXXFLAGS= -O0

# The C program compiler.
CC     = gcc

# The C++ program compiler.
CXX    = g++

# Un-comment the following line to compile C programs as C++ ones.
#CC     = $(CXX)

# The command used to delete file.
#RM     = rm -f

ETAGS = etags
ETAGSFLAGS =

CTAGS = ctags
CTAGSFLAGS =

## Stable Section: usually no need to be changed. But you can add more.
##==========================================================================
SHELL   = /bin/sh
EMPTY   =
SPACE   = $(EMPTY) $(EMPTY)

SOURCES = $(foreach d,$(SRCDIRS),$(wildcard $(addprefix $(d)/*,$(SRCEXTS))))
HEADERS = $(foreach d,$(SRCDIRS),$(wildcard $(addprefix $(d)/*,$(HDREXTS))))
SRC_CXX = $(filter-out %.c,$(SOURCES))
OBJS    = $(addsuffix .o, $(basename $(SOURCES)))
DEPS    = $(OBJS:.o=.d)

TEST_SOURCES = $(foreach d,$(TEST_SRCDIRS),$(wildcard $(addprefix $(d)/*,$(SRCEXTS)))) $(filter-out ./main.cpp,$(SOURCES))
TEST_HEADERS = $(foreach d,$(TEST_SRCDIRS),$(wildcard $(addprefix $(d)/*,$(HDREXTS))))
TEST_SRC_CXX = $(filter-out %.c,$(TEST_SOURCES))
TEST_OBJS    = $(addsuffix .o, $(basename $(TEST_SOURCES)))
TEST_DEPS    = $(TEST_OBJS:.o=.d)

## Define some useful variables.
DEP_OPT = $(shell if `$(CC) --version | grep "GCC" >/dev/null`; then \
                  echo "-MM -MP"; else echo "-M"; fi )
DEPEND      = $(CC)  $(DEP_OPT)  $(MY_CFLAGS) $(CFLAGS) $(CPPFLAGS)
COMPILE.c   = $(CC)  $(MY_CFLAGS) $(CFLAGS)   $(CPPFLAGS) -c
COMPILE.cxx = $(CXX) $(MY_CFLAGS) $(CXXFLAGS) $(CPPFLAGS) -c
LINK.c      = $(CC)  $(MY_CFLAGS) $(CFLAGS)   $(CPPFLAGS) $(LDFLAGS)
LINK.cxx    = $(CXX) $(MY_CFLAGS) $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS)

.PHONY: all objs clean distclean tags ctags help test

# Delete the default suffixes
.SUFFIXES:

all: $(PROGRAM)

# Rules for creating dependency files (.d).
#------------------------------------------

%.d:%.c
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.C
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.cc
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.cpp
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.CPP
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.c++
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.cp
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

%.d:%.cxx
	@echo -n $(dir $<) > $@
	@$(DEPEND) $< >> $@

# Rules for generating object files (.o).
#----------------------------------------
objs:$(OBJS)

%.o:%.c
	$(COMPILE.c) $< -o $@

%.o:%.C
	$(COMPILE.cxx) $< -o $@

%.o:%.cc
	$(COMPILE.cxx) $< -o $@

%.o:%.cpp
	$(COMPILE.cxx) $< -o $@

%.o:%.CPP
	$(COMPILE.cxx) $< -o $@

%.o:%.c++
	$(COMPILE.cxx) $< -o $@

%.o:%.cp
	$(COMPILE.cxx) $< -o $@

%.o:%.cxx
	$(COMPILE.cxx) $< -o $@

# Rules for generating the tags.
#-------------------------------------
tags: $(HEADERS) $(SOURCES) $(TEST_SOURCES)
	$(ETAGS) $(ETAGSFLAGS) $(HEADERS) $(SOURCES) $(TEST_SOURCES)

ctags: $(HEADERS) $(SOURCES) $(TEST_SOURCES)
	$(CTAGS) $(CTAGSFLAGS) $(HEADERS) $(SOURCES) $(TEST_SOURCES)

# Rules for generating the executable.
#-------------------------------------
$(PROGRAM):$(OBJS)
	$(LINK.cxx) $(OBJS) $(MY_LIBS) -o $@

test:$(TEST_OBJS)
	$(LINK.cxx) $(TEST_OBJS) $(MY_LIBS) -o $(TEST_PROGRAM)
	./$(TEST_PROGRAM)

ifndef NODEP
ifneq ($(DEPS),)
  sinclude $(DEPS)
endif
endif

clean:
	$(RM) $(OBJS) $(TEST_OBJS) $(PROGRAM) $(PROGRAM).exe $(TEST_PROGRAM) $(TEST_PROGRAM).exe

distclean: clean
	$(RM) $(DEPS) $(TEST_DEPS) TAGS

# Show help.
help:
	@echo 'Generic Makefile for C/C++ Programs (gcmakefile) version 0.4'
	@echo 'Copyright (C) 2007 whyglinux.'
	@echo
	@echo 'Usage: make [targets]'
	@echo 'Targets:'
	@echo '  all       (=make) compile and link.'
	@echo '  NODEP=yes make without generating dependencies.'
	@echo '  objs      compile only (no linking.)'
	@echo '  tags      create tags for Emacs.'
	@echo '  ctags     create ctags for VI.'
	@echo '  clean     clean objects and the executable file.'
	@echo '  distclean clean objects, the executable and dependencies.'
	@echo '  show      show variables (for debug use only.)'
	@echo '  help      print this message.'
	@echo
	@echo 'Report bugs to <whyglinux AT gmail DOT com>.'

# Show variables (for debug use only.)
show:
	@echo 'PROGRAM     :' $(PROGRAM)
	@echo 'TEST_PROGRAM:' $(TEST_PROGRAM)
	@echo 'SRCDIRS     :' $(SRCDIRS)
	@echo 'TEST_SRCDIRS:' $(TEST_SRCDIRS)
	@echo 'HEADERS     :' $(HEADERS)
	@echo 'SOURCES     :' $(SOURCES)
	@echo 'TEST_SOURCES:' $(TEST_SOURCES)
	@echo 'SRC_CXX     :' $(SRC_CXX)
	@echo 'TEST_SRC_CXX:' $(TEST_SRC_CXX)
	@echo 'OBJS        :' $(OBJS)
	@echo 'TEST_OBJS   :' $(TEST_OBJS)
	@echo 'DEPS        :' $(DEPS)
	@echo 'TEST_DEPS   :' $(TEST_DEPS)
	@echo 'DEPEND      :' $(DEPEND)
	@echo 'COMPILE.c   :' $(COMPILE.c)
	@echo 'COMPILE.cxx :' $(COMPILE.cxx)
	@echo 'link.c      :' $(LINK.c)
	@echo 'link.cxx    :' $(LINK.cxx)

## End of the Makefile ##  Suggestions are welcome  ## All rights reserved ##
#############################################################################
