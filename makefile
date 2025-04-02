# Makefile of Modbus Communication
# Author: Emir
# Date: 18.03.2025
# Details:

BUILD_TYPE = $(RELEASE)
#BUILD_TYPE = $(DEBUG)

SRC_NAME:= main
TARGET_NAME:= my_prog

CC:= gcc
LD:= gcc

# Directories 
PROJ_ROOT_DIR:= .
OBJ_DIR:= $(PROJ_ROOT_DIR)/obj
INC_DIR:= $(PROJ_ROOT_DIR)/include
SRC_DIR:=$(PROJ_ROOT_DIR)/src
DEP_DIR:=$(PROJ_ROOT_DIR)/dep
BIN_DIR:=$(PROJ_ROOT_DIR)/bin

TARGET:=$(BIN_DIR)/$(TARGET_NAME)

# SRC:=./$(SRC_DIR)/$(SRC_NAME).c
# OBJ:=./$(OBJ_DIR)/$(SRC_NAME).o
# DEP:=./$(DEP_DIR)/$(SRC_NAME).d,

# Src, obj and dep files
SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(SRCS:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)
DEPS = $(OBJS:$(OBJ_DIR)/%.o=$(DEP_DIR)/%.d)

# We want to check if any include is added to amn included dependency file
# with keeping track of any header that is changed we can see if any dependency changed
HEADERS=$(wildcard $(INC_DIR)/*.h) # Taking all of the headers

########## CC FLAGS ##########
# STDFLAG = -std=c11
# This has beed added for POSIX Compatibility
STDFLAG = -std=gnu1x

INC:=-I$(INC_DIR)

#choose release/debug
DEBUG = -pipe -g -Wall -W -fPIC
RELEASE = -pipe -O2 -Wall -W -fPIC

# -D stands for DEFINE. If want to define any macro which is used in code for \
    #  timestamp or git revision etc, can be used in this way.
DEFINES = -DBUILD_TIMESTAMP_STR=\"$(BUILD_TIMESTAMP)\" \
	  -DINSTALLATION_PATH_STR=\"$(INSTALLATION_PATH)\"

#UNCOMMENT IF LIKE TO SEE FOLLOWING WARNINGS. ATLEAST ONCE THIS NEEDS TO BE RUN\
FOR EACH MODULE
WARN=-Wall -Wextra -Werror -Wwrite-strings -Wno-parentheses \
     -pedantic -Warray-bounds -Wno-unused-variable -Wno-unused-function \
     -Wno-unused-parameter -Wno-unused-result

CCFLAGS = $(STDFLAG) $(BUILD_TYPE) $(DEFINES) $(WARN) $(INC)

########## CC FLAGS END ##########

########## LINKER FLAGS ##########
# LIBRARY_DIR= $(PROJ_ROOT_DIR)/libs
# LIBRARY:=linked_list
# DEP_LIBS = -L$(LIBRARY_DIR) -l$(LIBRARY) -lcheck -lsubunit -pthread -lrt -lm
									
#DEP_LIBS = -lcheck

# RPATH IS USED FOR LINKING USER DEFINED LIBS IN SPECIFIC PATH DURING
# BUILDING THE MODULE.It is needed for the User of the .so. \
    # Unit test binary may use it.
#RPATH="-Wl,-rpath,$(TARGET_DIR):$(TARGET_DIR)/3rd_party_lib"

#RPATH="-Wl,-rpath,$(TARGET_DIR)"

LDFLAGS = $(DEP_LIBS) $(RPATH)
LDFLAGS_PROFILING = $(DEP_LIBS) $(RPATH) -pgbu

########## LINKER FLAGS END ##########

# It creates target
$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $(TARGET)

# it creates obj files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CCFLAGS) -c $< -o $@

$(DEP_DIR)/%.d:$(SRC_DIR)/%.c $(HEADERS)
	$(CC) $(CCFLAGS) -M $(SRCS) > $@

# automatically include contents of .dep files
-include $(DEPS)

build_dependencies: $(DEPS)

run:
	$(TARGET)

build_dir:
	mkdir -p $(DEP_DIR)
	mkdir -p $(OBJ_DIR)
	mkdir -p $(BIN_DIR)

clean:
# rm -rf $(OBJ_DIR)
	rm -f $(DEP_DIR)/*
	rm -f $(BIN_DIR)/*
	rm -f $(OBJ_DIR)/*

.phony: build_dir build_dependencies install clean run