LIBS = -lm -lpthread -lcrypto

CC = gcc
CFLAGS = -g -Wall -O0 -I./include

.PHONY: clean all default

default: log_test logging_lib

all: default

#SOURCES = lib/log_service.c lib/log_context.c lib/queue.c test/main.c test/logger_test.c test/queue_test.c
LIB_SOURCES = $(wildcard lib/*.c) 
TEST_SOURCES = $(wildcard test/*.c)
SOURCES = ${LIB_SOURCES} ${TEST_SOURCES}

OBJECTS = $(patsubst %.c, %.o, ${SOURCES} )
LIB_OBJECTS = $(patsubst %.c, %.o, ${LIB_SOURCES} )
HEADERS = $(wildcard lib/*.h) $(wildcard test/*.h)
$(info "SOURCES:" ${SOURCES})
$(info "OBJECTS:" ${OBJECTS})
$(info "HEADERS is:" ${HEADERS})

%.o: %.c #${OBJECTS}: ${SOURCES} # $(HEADERS) #${OBJECTS}: ${SOURCES} $(HEADERS)
	@echo "SRC,OBJ $< $@ $% $^"
	$(CC) $(CFLAGS) -o $@  -c $< 

.PRECIOUS: $(TARGET) $(OBJECTS)

log_test: $(OBJECTS) $(HEADERS)
	@echo "TARGET $@, $<"
	$(CC) -Wall $(LIBS) -o test/$@  $(OBJECTS) ${LIBS}

logging_lib: ${LIB_OBJECTS}
	@echo "Creating logging library lib/logging.a"
	ar rcs logging.a $(LIB_OBJECTS)

debug_log_test:	
	log_test
	
clean:
	-rm -f lib/*.o
	-rm -f test/*.o
	-rm -f test/log_test
	-rm -rf lib/logging.a
