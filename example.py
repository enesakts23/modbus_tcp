"""
Modbus TCP İstemci Örneği - C kodundan port edilmiştir
"""

from modbus import ModbusClient, ModbusError
from register_map import (
    CoilAddresses,
    DiscreteInputAddresses,
    HoldingRegisters,
    InputRegisters,
    CoilValues
)

def main():
    # Modbus istemcisi oluştur
    client = ModbusClient()
    
    # Sunucuya bağlan
    if not client.connect("localhost", 1024):
        print("Sunucuya bağlanılamadı")
        return
    
    print("Sunucuya bağlandı")
    
    try:
        # Örnek 1: Coil okuma (C kodundaki örnekler)
        error, coils = client.read_coils(0, 10)
        if error == ModbusError.OK:
            print("\nCoil Değerleri:")
            for addr, value in enumerate(coils):
                if addr in [CoilAddresses.COIL_2, CoilAddresses.COIL_3,
                          CoilAddresses.COIL_8, CoilAddresses.COIL_9]:
                    print(f"  Coil {addr}: {'ON' if value else 'OFF'}")
        else:
            print(f"Coil okuma hatası: {error}")
            
        # Örnek 2: Holding Register okuma
        error, registers = client.read_holding_registers(0, 2)  # İlk iki register
        if error == ModbusError.OK:
            print("\nHolding Register Değerleri:")
            for addr, value in enumerate(registers):
                print(f"  Register {addr}: 0x{value:04X}")
        else:
            print(f"Register okuma hatası: {error}")
            
        # Örnek 3: Tek coil yazma
        error = client.write_single_coil(CoilAddresses.COIL_2, True)
        if error == ModbusError.OK:
            print(f"\nCoil {CoilAddresses.COIL_2} başarıyla yazıldı (ON)")
        else:
            print(f"Coil yazma hatası: {error}")
            
        # Örnek 4: Tek register yazma
        new_value = 0x5555
        error = client.write_single_register(HoldingRegisters.REGISTER_0, new_value)
        if error == ModbusError.OK:
            print(f"\nRegister {HoldingRegisters.REGISTER_0} başarıyla yazıldı (0x{new_value:04X})")
        else:
            print(f"Register yazma hatası: {error}")
            
        # Örnek 5: Çoklu coil yazma
        coil_values = [True, False, True, True, False]
        error = client.write_multiple_coils(5, coil_values)
        if error == ModbusError.OK:
            print("\nÇoklu coil yazma başarılı")
        else:
            print(f"Çoklu coil yazma hatası: {error}")
            
        # Örnek 6: Çoklu register yazma
        register_values = [0x1111, 0x2222, 0x3333]
        error = client.write_multiple_registers(5, register_values)
        if error == ModbusError.OK:
            print("\nÇoklu register yazma başarılı")
        else:
            print(f"Çoklu register yazma hatası: {error}")
            
    except Exception as e:
        print(f"Hata oluştu: {e}")
    
    finally:
        # Bağlantıyı kapat
        client.close()
        print("\nBağlantı kapatıldı")

if __name__ == "__main__":
    main()