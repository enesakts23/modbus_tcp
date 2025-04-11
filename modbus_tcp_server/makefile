CCFLAGS += $(shell pkg-config --cflags libmodbus)
LDFLAGS += $(shell pkg-config --libs libmodbus)

build:
	gcc -o modbus_test modbus_test.c $(CCFLAGS) $(LDFLAGS)

clean:
	rm modbus_test

run:
	./modbus_test