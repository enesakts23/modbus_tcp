"""
C kodundan port edilmiş Modbus TCP Master (Client)
Bu sınıf komut gönderen ve veri talep eden taraftır
"""
from enum import Enum
import struct
import time
from typing import Tuple, List, Optional
from tcp_client import TCPClient

# C kodundaki sabitler
MODBUS_RECEIVE_MAX_DATA_SIZE = 251
MODBUS_WRITE_MULT_REQ_MAX_DATA_SIZE = 247
MODBUS_TCP_MAX_ADU_LENGTH = 260  # 7 (MBAP) + 253 (PDU)

class ModbusFunctions(Enum):
    """C kodundaki modbus_functions_t"""
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10

class CoilValue(Enum):
    """C kodundaki write_single_coil_value_t"""
    COIL_OFF = 0x0000
    COIL_ON = 0xFF00

class ModbusError(Enum):
    """C kodundaki modbus_req_return_val_t ve modbus_response_return_val_t birleşimi"""
    OK = 0
    GENERAL_ERROR = 1
    ILLEGAL_FUNCTION = 2
    ILLEGAL_ADDRESS = 3
    ILLEGAL_VALUE = 4
    COMMUNICATION_ERROR = 5
    NO_RESPONSE = 6
    WRONG_DATA = 7

class ModbusMaster:
    def __init__(self):
        self.tcp_client = TCPClient()
        self.transaction_id = 0

    def connect(self, host: str, port: int = 502) -> bool:
        """Modbus Slave'e bağlan"""
        if self.tcp_client.init(host, port) != 0:
            return False
        return self.tcp_client.connect_to_server() == 0

    def _build_mbap_header(self, function: ModbusFunctions, data_length: int) -> bytes:
        """C kodundaki MBAP header oluşturma"""
        self.transaction_id = (self.transaction_id + 1) % 65536
        unit_id = 0x01  # Varsayılan unit ID
        length = data_length + 2  # Fonksiyon kodu (1) + Unit ID (1) + Data Length
        
        return struct.pack('>HHHBB',
            self.transaction_id,  # Transaction ID (2 bytes)
            0,                    # Protocol ID (2 bytes, always 0)
            length,               # Length (2 bytes)
            unit_id,             # Unit ID (1 byte)
            function.value       # Function code (1 byte)
        )

    def read_coils(self, address: int, count: int) -> Tuple[ModbusError, List[bool]]:
        """C kodundaki read_coils karşılığı"""
        if count > 2000:  # Modbus spesifikasyonu limiti
            return ModbusError.ILLEGAL_VALUE, []

        # İstek oluştur
        request = self._build_mbap_header(ModbusFunctions.READ_COILS, 4)
        request += struct.pack('>HH', address, count)

        # İsteği gönder
        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR, []

        # Yanıt bekle
        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 9:  # MBAP (7) + Function (1) + Byte Count (1)
            return ModbusError.COMMUNICATION_ERROR, []

        # Yanıtı işle
        try:
            function_code = response[7]
            if function_code & 0x80:  # Hata yanıtı
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

    def read_holding_registers(self, address: int, count: int) -> Tuple[ModbusError, List[int]]:
        """C kodundaki read_holding_registers karşılığı"""
        if count > 125:  # Modbus spesifikasyonu limiti
            return ModbusError.ILLEGAL_VALUE, []

        # İstek oluştur
        request = self._build_mbap_header(ModbusFunctions.READ_HOLDING_REGISTERS, 4)
        request += struct.pack('>HH', address, count)

        # İsteği gönder
        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR, []

        # Yanıt bekle
        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 9:
            return ModbusError.COMMUNICATION_ERROR, []

        # Yanıtı işle
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

    def write_single_coil(self, address: int, value: bool) -> ModbusError:
        """C kodundaki write_single_coil karşılığı"""
        coil_value = CoilValue.COIL_ON.value if value else CoilValue.COIL_OFF.value
        
        # İstek oluştur
        request = self._build_mbap_header(ModbusFunctions.WRITE_SINGLE_COIL, 4)
        request += struct.pack('>HH', address, coil_value)

        # İsteği gönder
        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıt bekle
        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 8:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıtı kontrol et
        function_code = response[7]
        if function_code & 0x80:
            return ModbusError.ILLEGAL_FUNCTION

        return ModbusError.OK

    def write_single_register(self, address: int, value: int) -> ModbusError:
        """C kodundaki write_single_register karşılığı"""
        if not 0 <= value <= 0xFFFF:
            return ModbusError.ILLEGAL_VALUE

        # İstek oluştur
        request = self._build_mbap_header(ModbusFunctions.WRITE_SINGLE_REGISTER, 4)
        request += struct.pack('>HH', address, value)

        # İsteği gönder
        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıt bekle
        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 8:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıtı kontrol et
        function_code = response[7]
        if function_code & 0x80:
            return ModbusError.ILLEGAL_FUNCTION

        return ModbusError.OK

    def write_multiple_coils(self, address: int, values: List[bool]) -> ModbusError:
        """C kodundaki write_multiple_coils karşılığı"""
        if len(values) > 1968:  # Modbus spesifikasyonu limiti
            return ModbusError.ILLEGAL_VALUE

        # Coil değerlerini byte dizisine dönüştür
        byte_count = (len(values) + 7) // 8
        coil_bytes = bytearray(byte_count)
        
        for i, value in enumerate(values):
            if value:
                coil_bytes[i // 8] |= (0x01 << (i % 8))

        # İstek oluştur
        request = self._build_mbap_header(ModbusFunctions.WRITE_MULTIPLE_COILS, 5 + byte_count)
        request += struct.pack('>HHB', address, len(values), byte_count)
        request += coil_bytes

        # İsteği gönder
        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıt bekle
        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 8:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıtı kontrol et
        function_code = response[7]
        if function_code & 0x80:
            return ModbusError.ILLEGAL_FUNCTION

        return ModbusError.OK

    def write_multiple_registers(self, address: int, values: List[int]) -> ModbusError:
        """C kodundaki write_multiple_registers karşılığı"""
        if len(values) > 123:  # Modbus spesifikasyonu limiti
            return ModbusError.ILLEGAL_VALUE

        for value in values:
            if not 0 <= value <= 0xFFFF:
                return ModbusError.ILLEGAL_VALUE

        # Register değerlerini byte dizisine dönüştür
        register_bytes = bytearray()
        for value in values:
            register_bytes.extend(struct.pack('>H', value))

        # İstek oluştur
        byte_count = len(values) * 2
        request = self._build_mbap_header(ModbusFunctions.WRITE_MULTIPLE_REGISTERS, 5 + byte_count)
        request += struct.pack('>HHB', address, len(values), byte_count)
        request += register_bytes

        # İsteği gönder
        if self.tcp_client.send_data_to_server(request) != 0:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıt bekle
        status, response, size = self.tcp_client.receive_data_from_server()
        if status != 0 or size < 8:
            return ModbusError.COMMUNICATION_ERROR

        # Yanıtı kontrol et
        function_code = response[7]
        if function_code & 0x80:
            return ModbusError.ILLEGAL_FUNCTION

        return ModbusError.OK

    def close(self):
        """C kodundaki close_connection karşılığı"""
        self.tcp_client.close_connection()