from enum import IntEnum

class BMSRegisters(IntEnum):
    # 32-bit float çiftleri
    SOC = 1000                        # SOC (1000-1001)
    SOC_HIGH = 1000
    SOC_LOW = 1001
    SOH = 1002                        # SOH (1002-1003)
    SOH_HIGH = 1002
    SOH_LOW = 1003
    TOTAL_VOLTAGE = 1004              # Total Voltage (1004-1005)
    TOTAL_VOLTAGE_HIGH = 1004
    TOTAL_VOLTAGE_LOW = 1005
    MAX_TEMPERATURE = 1006            # Max Temperature (1006-1007)
    MAX_TEMPERATURE_HIGH = 1006
    MAX_TEMPERATURE_LOW = 1007
    CURRENT = 1008                    # Current (1008-1009)
    CURRENT_HIGH = 1008
    CURRENT_LOW = 1009

    AVERAGE_VOLTAGE = 1012            # Average Voltage (1012-1013)
    AVERAGE_VOLTAGE_HIGH = 1012
    AVERAGE_VOLTAGE_LOW = 1013
    AVERAGE_TEMPERATURE = 1014        # Average Temperature (1014-1015)
    AVERAGE_TEMPERATURE_HIGH = 1014
    AVERAGE_TEMPERATURE_LOW = 1015

    CELL_VOLTAGE_BASE = 1016          # Her hücre 2 register (32-bit float)
    TEMP_SENSOR_BASE = 7000           # Her sensör 2 register (32-bit float)

class BMSAddressCalculator:
    @staticmethod
    def get_cell_voltage_address(string_no: int, packet_no: int, cell_no: int) -> int:
        if not (1 <= string_no <= 12):
            raise ValueError("String no 1-12 arası olmalı")
        if not (1 <= packet_no <= 4):
            raise ValueError("Packet no 1-4 arası olmalı")
        if not (1 <= cell_no <= 104):
            raise ValueError("Cell no 1-104 arası olmalı")
        
        base_address = BMSRegisters.CELL_VOLTAGE_BASE
        # Her hücre 2 register (32-bit float)
        offset = (string_no - 1) * 4 * 104 * 2 + (packet_no - 1) * 104 * 2 + (cell_no - 1) * 2
        return base_address + offset
    
    @staticmethod
    def get_temperature_address(string_no: int, packet_no: int, bms_no: int, sensor_no: int) -> int:
        if not (1 <= string_no <= 12):
            raise ValueError("String no 1-12 arası olmalı")
        if not (1 <= packet_no <= 4):
            raise ValueError("Packet no 1-4 arası olmalı")
        if not (1 <= bms_no <= 6):
            raise ValueError("BMS no 1-6 arası olmalı")
        if not (1 <= sensor_no <= 8):
            raise ValueError("Sensor no 1-8 arası olmalı")
        
        base_address = BMSRegisters.TEMP_SENSOR_BASE
        # Her sıcaklık 2 register (32-bit float)
        offset = (string_no - 1) * 4 * 6 * 8 * 2 + (packet_no - 1) * 6 * 8 * 2 + (bms_no - 1) * 8 * 2 + (sensor_no - 1) * 2
        return base_address + offset
    
    @staticmethod
    def get_balancing_status_address(string_no: int, packet_no: int, cell_no: int) -> int:
        if not (1 <= string_no <= 12):
            raise ValueError("String no 1-12 arası olmalı")
        if not (1 <= packet_no <= 4):
            raise ValueError("Packet no 1-4 arası olmalı")
        if not (1 <= cell_no <= 104):
            raise ValueError("Cell no 1-104 arası olmalı")
        
        base_address = 40000  # Balancing status base
        # Balancing durumu bit tabanlı, hala tek register
        offset = (string_no - 1) * 4 * 104 + (packet_no - 1) * 104 + (cell_no - 1)
        return base_address + offset
    
    @staticmethod
    def parse_cell_address(address: int) -> tuple:
        if address < BMSRegisters.CELL_VOLTAGE_BASE:
            raise ValueError("Geçersiz hücre adresi")
        offset = (address - BMSRegisters.CELL_VOLTAGE_BASE) // 2  # 32-bit float için 2'ye böl
        string_no = offset // (4 * 104) + 1
        remaining = offset % (4 * 104)
        packet_no = remaining // 104 + 1
        cell_no = remaining % 104 + 1
        return string_no, packet_no, cell_no
    
    @staticmethod
    def parse_temp_address(address: int) -> tuple:
        if address < BMSRegisters.TEMP_SENSOR_BASE:
            raise ValueError("Geçersiz sıcaklık adresi")
        offset = (address - BMSRegisters.TEMP_SENSOR_BASE) // 2  # 32-bit float için 2'ye böl
        string_no = offset // (4 * 6 * 8) + 1
        remaining = offset % (4 * 6 * 8)
        packet_no = remaining // (6 * 8) + 1
        remaining = remaining % (6 * 8)
        bms_no = remaining // 8 + 1
        sensor_no = remaining % 8 + 1
        return string_no, packet_no, bms_no, sensor_no

class BMSInputs(IntEnum):
    pass

class BMSCoils(IntEnum):
    # 32-bit float çiftleri
    AVG_TEMP = 30003              # Average Temperature (30003-30004)
    AVG_TEMP_HIGH = 30003
    AVG_TEMP_LOW = 30004
    AVG_CELLV = 30005             # Average Cell Voltage (30005-30006)
    AVG_CELLV_HIGH = 30005
    AVG_CELLV_LOW = 30006
    PACK_VOLT = 30007             # Pack Voltage (30007-30008)
    PACK_VOLT_HIGH = 30007
    PACK_VOLT_LOW = 30008   

class BMSDataConverter:
    @staticmethod
    def float_to_registers(value: float) -> tuple:
        """32-bit float'ı 2 register'a çevir"""
        import struct
        # IEEE 754 formatında 32-bit float'ı bytes'a çevir
        bytes_data = struct.pack('>f', value)  # Big-endian
        # Bytes'ı 2 register'a böl
        high_reg = int.from_bytes(bytes_data[:2], 'big')
        low_reg = int.from_bytes(bytes_data[2:], 'big')
        return high_reg, low_reg
    
    @staticmethod
    def registers_to_float(high_reg: int, low_reg: int) -> float:
        """2 register'ı 32-bit float'a çevir"""
        import struct
        # Register'ları bytes'a çevir
        bytes_data = high_reg.to_bytes(2, 'big') + low_reg.to_bytes(2, 'big')
        # Bytes'ı float'a çevir
        return struct.unpack('>f', bytes_data)[0]
    
    @staticmethod
    def voltage_to_raw(voltage_v: float) -> int:
        return int(voltage_v * 10)
    
    @staticmethod
    def raw_to_voltage(raw: int) -> float:
        return raw / 10.0
    
    @staticmethod
    def current_to_raw(current_a: float) -> int:
        return int(current_a * 10)
    
    @staticmethod
    def raw_to_current(raw: int) -> float:
        if raw > 32767:
            raw = raw - 65536
        return raw / 10.0
    
    @staticmethod
    def temp_to_raw(temp_c: float) -> int:
        return int(temp_c + 40)
    def raw_to_temp(raw: int) -> float:
        return raw - 40
    
    @staticmethod
    def cell_voltage_to_raw(voltage_v: float) -> int:
        return int(voltage_v * 1000)
    
    @staticmethod
    def raw_to_cell_voltage(raw: int) -> float:
        return raw / 1000.0

BMS_INITIAL_VALUES = {

    BMSRegisters.SOC_HIGH: 0x42B1, 
    BMSRegisters.SOC_LOW: 0x0000,   
    BMSRegisters.SOH_HIGH: 0x42C5,  
    BMSRegisters.SOH_LOW: 0x8000,  
    BMSRegisters.TOTAL_VOLTAGE_HIGH: 0x43C9,  
    BMSRegisters.TOTAL_VOLTAGE_LOW: 0x999A,  
    BMSRegisters.MAX_TEMPERATURE_HIGH: 0x41CC,  
    BMSRegisters.MAX_TEMPERATURE_LOW: 0x0000,  
    BMSRegisters.CURRENT_HIGH: 0xC296,  
    BMSRegisters.CURRENT_LOW: 0x0000,  
}

BMS_INPUT_VALUES = {}
BMS_COIL_VALUES = {

    BMSCoils.AVG_TEMP_HIGH: 0x41CE,    
    BMSCoils.AVG_TEMP_LOW: 0x6666,     
    
    BMSCoils.AVG_CELLV_HIGH: 0x4069,   
    BMSCoils.AVG_CELLV_LOW: 0x999A,    
    
    BMSCoils.PACK_VOLT_HIGH: 0x43C9,  
    BMSCoils.PACK_VOLT_LOW: 0x999A,  
}
