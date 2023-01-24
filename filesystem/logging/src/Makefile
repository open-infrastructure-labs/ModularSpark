LIBS = -lm -lpthread

CC = gcc
CFLAGS = -g -Wall -O0 -I./include

.PHONY: clean all default

default: log_test

all: default

SOURCES = lib/log_service.c lib/log_context.c lib/queue.c test/main.c test/logger_test.c test/queue_test.c

OBJECTS = $(patsubst %.c, %.o, ${SOURCES})
HEADERS = $(wildcard *.h)
$(info "SOURCES is:" ${SOURCES})
$(info "OBJECTS is:" ${OBJECTS})
$(info "HEADERS is:" ${HEADERS})

%.o: %.c #${OBJECTS}: ${SOURCES} # $(HEADERS) #${OBJECTS}: ${SOURCES} $(HEADERS)
	@echo "SRC,OBJ $< $@ $% $^"
	$(CC) $(CFLAGS) -o $@  -c $< 

.PRECIOUS: $(TARGET) $(OBJECTS)

log_test: $(OBJECTS)
	@echo "TARGET $@, $<"
	$(CC) -Wall $(LIBS) -o test/$@  $(OBJECTS) ${LIBS}

debug_log_test:	
	log_test
	
clean:
	-rm -f lib/*.o
	-rm -f test/*.o
	-rm -f test/log_test
