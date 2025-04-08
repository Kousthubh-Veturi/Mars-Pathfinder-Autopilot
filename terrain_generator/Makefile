CC = g++
CFLAGS = -Wall -O3 -fPIC -std=c++14
TARGET = libterrain_generator.so

all: $(TARGET)

$(TARGET): terrain_generator.cpp
	$(CC) $(CFLAGS) -shared -o $@ $<

clean:
	rm -f $(TARGET) *.o 