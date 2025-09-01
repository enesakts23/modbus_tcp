"""
Modbus Register Haritası - C kodundan port edilmiştir
"""
from enum import IntEnum

# Modbus Fonksiyon Kodları
class ModbusFunctions(IntEnum):
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10

# Coil Değerleri
class CoilValues(IntEnum):
    COIL_OFF = 0x0000
    COIL_ON = 0xFF00

# Coil Adresleri (0x01)
class CoilAddresses(IntEnum):
    COIL_2 = 2  # Test coil 2
    COIL_3 = 3  # Test coil 3
    COIL_8 = 8  # Test coil 8
    COIL_9 = 9  # Test coil 9

# Discrete Input Adresleri (0x02)
class DiscreteInputAddresses(IntEnum):
    INPUT_0 = 0  # İlk input "HIGH"
    INPUT_1 = 1  # İkinci input "LOW"
    INPUT_2 = 2  # Üçüncü input "HIGH"
    INPUT_6 = 6  # Test input 6
    INPUT_7 = 7  # Test input 7
    INPUT_9 = 9  # Test input 9

# Holding Register Adresleri (0x03)
class HoldingRegisters(IntEnum):
    REGISTER_0 = 0  # Test register 0 (0x1234)
    REGISTER_1 = 1  # Test register 1 (0x5678)

# Input Register Adresleri (0x04)
class InputRegisters(IntEnum):
    REGISTER_2 = 2  # Test register 2 (0x9ABC)
    REGISTER_3 = 3  # Test register 3 (0xDEF1)

# Başlangıç Değerleri
INITIAL_VALUES = {
    # Coil başlangıç değerleri
    'coils': {
        CoilAddresses.COIL_2: True,
        CoilAddresses.COIL_3: True,
        CoilAddresses.COIL_8: True,
        CoilAddresses.COIL_9: True
    },
    # Discrete Input başlangıç değerleri
    'discrete_inputs': {
        DiscreteInputAddresses.INPUT_0: True,
        DiscreteInputAddresses.INPUT_1: False,
        DiscreteInputAddresses.INPUT_2: True,
        DiscreteInputAddresses.INPUT_6: True,
        DiscreteInputAddresses.INPUT_7: True,
        DiscreteInputAddresses.INPUT_9: True
    },
    # Holding Register başlangıç değerleri
    'holding_registers': {
        HoldingRegisters.REGISTER_0: 0x1234,
        HoldingRegisters.REGISTER_1: 0x5678
    },
    # Input Register başlangıç değerleri
    'input_registers': {
        InputRegisters.REGISTER_2: 0x9ABC,
        InputRegisters.REGISTER_3: 0xDEF1
    }
}