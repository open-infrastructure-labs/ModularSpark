TARGET = fuse_pass_thru
# LIBS = -lm `pkg-config fuse3 --cflags --libs` -L../../logging/src -l:logging.a -lcrypto 
LIBS = -lm `pkg-config fuse3 --cflags --libs`
CC = gcc
CFLAGS = -g -Wall -ggdb 

.PHONY: default all clean

default: $(TARGET)
all: default

OBJECTS = $(patsubst %.c, %.o, $(wildcard *.c))
HEADERS = $(wildcard *.h)

%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

.PRECIOUS: $(TARGET) $(OBJECTS)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -Wall $(LIBS) -o $@

clean:
	-rm -f *.o
	-rm -f $(TARGET)