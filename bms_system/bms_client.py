from enum import Enum
import struct
import time
from typing import Tuple, List, Optional
import socket
import select

# TCP Client sınıfı
class TCPClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.address_info = None
        self.connected = False

    def init(self, connection_address: str, port_number: int) -> int:

        try:
            self.address_info = socket.getaddrinfo(connection_address, port_number, 
                                                 socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not self.address_info:
                return -1
                
            family, socktype, proto, _, addr = self.address_info[0]
            self.socket = socket.socket(family, socktype, proto)
            if not self.socket:
                return -2
                
            return 0
            
        except socket.gaierror:
            return -1
        except socket.error:
            return -2

    def connect_to_server(self) -> int:

        if not self.socket or not self.address_info:
            return -1

        try:
            self.socket.settimeout(0.5)
            _, _, _, _, addr = self.address_info[0]
            self.socket.connect(addr)
            self.connected = True
            return 0
            
        except (socket.timeout, socket.error):
            return -1

    def send_data_to_server(self, data: bytes) -> int:
        """Send data to server"""
        if not self.socket or not self.connected:
            return -1

        try:
            self.socket.sendall(data)
            return 0
        except socket.error:
            return -1

    def receive_data_from_server(self) -> Tuple[int, bytes, int]:

        if not self.socket or not self.connected:
            return -1, b'', 0

        try:
            data = self.socket.recv(260)
            if not data:
                return -1, b'', 0
            return 0, data, len(data)
        except socket.error:
            return -1, b'', 0

    def close_connection(self):
    
        if self.socket:
            try:
                self.socket.close()
            except socket.error:
                pass
            finally:
                self.socket = None
                self.address_info = None
                self.connected = False


class ModbusFunctions(Enum):
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10

class ModbusError(Enum):
    OK = 0
    GENERAL_ERROR = 1
    ILLEGAL_FUNCTION = 2
    ILLEGAL_ADDRESS = 3
    ILLEGAL_VALUE = 4
    COMMUNICATION_ERROR = 5
    NO_RESPONSE = 6
    WRONG_DATA = 7

class CoilValue(Enum):
    COIL_OFF = 0x0000
    COIL_ON = 0xFF00

class BMSMaster:
    def __init__(self):
        self.tcp_client = TCPClient()
        self.transaction_id = 0

    def connect(self, host: str, port: int = 502) -> bool:
        """BMS Slave'e bağlan"""
        if self.tcp_client.init(host, port) != 0:
            return False
        return self.tcp_client.connect_to_server() == 0

    def _build_mbap_header(self, function: ModbusFunctions, data_length: int) -> bytes:
        """MBAP header oluştur"""
        self.transaction_id = (self.transaction_id + 1) % 65536
        unit_id = 0x01
        length = data_length + 2
        
        return struct.pack('>HHHBB',
            self.transaction_id,
            0,
            length,
            unit_id,
            function.value
        )

    def read_holding_registers(self, address: int, count: int) -> Tuple[ModbusError, List[int]]:
        """Holding register oku"""
        if count > 125:
            return ModbusError.ILLEGAL_VALUE, []

        request = self._build_mbap_header(ModbusFunctions.READ_HOLDING_REGISTERS, 4)
        request += struct.pack('>HH', address, count)

        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR, []

        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 9:
            return ModbusError.COMMUNICATION_ERROR, []

        try:
            function_code = response[7]
            if function_code & 0x80:
                return ModbusError.ILLEGAL_FUNCTION, []

            byte_count = response[8]
            if byte_count != count * 2:
                return ModbusError.WRONG_DATA, []

            register_data = response[9:9+byte_count]
            register_values = []
            
            for i in range(0, byte_count, 2):
                value = struct.unpack('>H', register_data[i:i+2])[0]
                register_values.append(value)

            return ModbusError.OK, register_values
        except:
            return ModbusError.WRONG_DATA, []

    def read_discrete_inputs(self, address: int, count: int) -> Tuple[ModbusError, List[bool]]:
        """Discrete input oku"""
        if count > 2000:
            return ModbusError.ILLEGAL_VALUE, []

        request = self._build_mbap_header(ModbusFunctions.READ_DISCRETE_INPUTS, 4)
        request += struct.pack('>HH', address, count)

        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR, []

        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 9:
            return ModbusError.COMMUNICATION_ERROR, []

        try:
            function_code = response[7]
            if function_code & 0x80:
                return ModbusError.ILLEGAL_FUNCTION, []

            byte_count = response[8]
            input_data = response[9:9+byte_count]
            
            input_values = []
            for i in range(count):
                byte_index = i // 8
                bit_index = i % 8
                if byte_index < byte_count:
                    input_values.append(bool(input_data[byte_index] & (0x01 << bit_index)))

            return ModbusError.OK, input_values
        except:
            return ModbusError.WRONG_DATA, []

    def read_coils(self, address: int, count: int) -> Tuple[ModbusError, List[bool]]:
        """Coil oku"""
        if count > 2000:
            return ModbusError.ILLEGAL_VALUE, []

        request = self._build_mbap_header(ModbusFunctions.READ_COILS, 4)
        request += struct.pack('>HH', address, count)

        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR, []

        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 9:
            return ModbusError.COMMUNICATION_ERROR, []

        try:
            function_code = response[7]
            if function_code & 0x80:
                return ModbusError.ILLEGAL_FUNCTION, []

            byte_count = response[8]
            coil_data = response[9:9+byte_count]
            
            coil_values = []
            for i in range(count):
                byte_index = i // 8
                bit_index = i % 8
                if byte_index < byte_count:
                    coil_values.append(bool(coil_data[byte_index] & (0x01 << bit_index)))

            return ModbusError.OK, coil_values
        except:
            return ModbusError.WRONG_DATA, []

    def write_single_register(self, address: int, value: int) -> ModbusError:
        """Tek register yaz"""
        if not 0 <= value <= 0xFFFF:
            return ModbusError.ILLEGAL_VALUE

        request = self._build_mbap_header(ModbusFunctions.WRITE_SINGLE_REGISTER, 4)
        request += struct.pack('>HH', address, value)

        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR

        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 8:
            return ModbusError.COMMUNICATION_ERROR

        function_code = response[7]
        if function_code & 0x80:
            return ModbusError.ILLEGAL_FUNCTION

        return ModbusError.OK

    def write_single_coil(self, address: int, value: bool) -> ModbusError:
        """Tek coil yaz"""
        coil_value = CoilValue.COIL_ON.value if value else CoilValue.COIL_OFF.value
        
        request = self._build_mbap_header(ModbusFunctions.WRITE_SINGLE_COIL, 4)
        request += struct.pack('>HH', address, coil_value)

        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR

        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 8:
            return ModbusError.COMMUNICATION_ERROR

        function_code = response[7]
        if function_code & 0x80:
            return ModbusError.ILLEGAL_FUNCTION

        return ModbusError.OK

    def close(self):
        """Bağlantıyı kapat"""
        self.tcp_client.close_connection()
