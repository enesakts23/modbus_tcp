# modbus_tcp
Modbus TCP Client Project with modular structure to use with any kind of TCP Communication.
The purpose of this library is having a library that can be used with any device(for example; STM)
or technology(for example; Qt) that has tcp/ip communication ability.
It includes functions to connect and manipulate modbus server data and is built with `Make`. 
Unit tests are written using the `Check` testing framework.
Tests are made with a modbus server that runs on same device. That server is written with
`libmodbus` library. The code of server is in folders. Have to build and run it to
run unit tests.

## Usage

Details of usage can be found at function descriptions and in unit test.
Always check connection and returned errors. Don't forget to close connection. 

### Installation of Server

Details about server's library can be found at [`libmodbus`](https://libmodbus.org/)

Install libmodbus library with this command.

```bash
sudo apt install libmodbus-dev
```

go to server_code by

```bash
cd modbus_tcp_server
```

build by

```bash
make
```

run by

```bash
sudo make run
```

We are running it with sudo because we need superuser privileges to use port 502. 

### Testing

Tests are made with a unit test framework called [`Check`](https://libcheck.github.io/check/)
create test program with

installation instruction can be found [here](https://libcheck.github.io/check/web/install.html)

Test code can be run after starting server by using commands: 

```bash
make
make run
```
### Cleaning 

You can clean all the outputs of building by
```bash
make clean
```

## Future Improvements
Transaction ID is always the same and doesn't check returned transaction ID.
Additional code can be added to change transaction ID in every request and check the returning value to see if it matches or not.
Returned Fucntion Codes can be checked maybe.

### License
Any License didn't provided because it is not a open source project. Additional libraries like check and libmodbus is only
used in testing. So the code doesn't have any dependency on any library. Licensing can be made later.