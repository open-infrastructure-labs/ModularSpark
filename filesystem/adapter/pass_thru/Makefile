TARGET = fuse_pass_thru

ifeq (${LOGGING_ENABLE}, 1)
	LIBS = -lm `pkg-config fuse3 --cflags --libs` -L../../logging/src -l:logging.a -lcrypto
	DEFINES = 
else
	LIBS = -lm `pkg-config fuse3 --cflags --libs`
	DEFINES = -DDISABLE_LOGGER
endif

CC = gcc
CFLAGS = -g -Wall -ggdb 

.PHONY: default all clean

default: $(TARGET)
all: default

OBJECTS = $(patsubst %.c, %.o, $(wildcard *.c))
HEADERS = $(wildcard *.h)

%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) $(DEFINES) -c $< -o $@

.PRECIOUS: $(TARGET) $(OBJECTS)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -Wall $(LIBS) -o $@

clean:
	-rm -f *.o
	-rm -f $(TARGET)