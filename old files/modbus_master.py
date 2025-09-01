"""
Modbus TCP Master Örneği - C kodundan port edilmiştir
Bu script Master (komut gönderen) olarak çalışır
"""

from modbus import ModbusMaster, ModbusError
from register_map import (
    CoilAddresses,
    DiscreteInputAddresses,
    HoldingRegisters,
    InputRegisters,
    CoilValues
)

def main():
    print("=== MASTER (CLIENT) MODU ===")
    print("Bu cihaz komut gönderen olarak çalışıyor")
    print("Slave'den veri talep edecek ve komut gönderecek\n")
    
    # Modbus Master'ı oluştur
    master = ModbusMaster()
    
    # Slave'e bağlan
    if not master.connect("10.134.20.219", 1024):
        print("Slave'e bağlanılamadı")
        return
    
    print("Slave'e başarıyla bağlandı\n")
    
    try:
        # Örnek 1: Coil okuma (Slave'den veri talep et)
        error, coils = master.read_coils(0, 10)
        if error == ModbusError.OK:
            print("=== SLAVE'DEN OKUNAN COIL DEĞERLERİ ===")
            for addr, value in enumerate(coils):
                if addr in [CoilAddresses.COIL_2, CoilAddresses.COIL_3,
                          CoilAddresses.COIL_8, CoilAddresses.COIL_9]:
                    print(f"  Coil {addr}: {'ON' if value else 'OFF'}")
        else:
            print(f"Coil okuma hatası: {error}")
            
        # Örnek 2: Holding Register okuma
        error, registers = master.read_holding_registers(0, 2)  # İlk iki register
        if error == ModbusError.OK:
            print("\n=== SLAVE'DEN OKUNAN REGISTER DEĞERLERİ ===")
            for addr, value in enumerate(registers):
                print(f"  Register {addr}: 0x{value:04X}")
        else:
            print(f"Register okuma hatası: {error}")
            
        # Örnek 3: Tek coil yazma (Slave'e komut gönder)
        error = master.write_single_coil(CoilAddresses.COIL_2, True)
        if error == ModbusError.OK:
            print(f"\n=== SLAVE'E KOMUT GÖNDERİLDİ ===")
            print(f"Coil {CoilAddresses.COIL_2} başarıyla yazıldı (ON)")
        else:
            print(f"Coil yazma hatası: {error}")
            
        # Örnek 4: Tek register yazma
        new_value = 0x5555
        error = master.write_single_register(HoldingRegisters.REGISTER_0, new_value)
        if error == ModbusError.OK:
            print(f"Register {HoldingRegisters.REGISTER_0} başarıyla yazıldı (0x{new_value:04X})")
        else:
            print(f"Register yazma hatası: {error}")
            
        # Örnek 5: Çoklu coil yazma
        coil_values = [True, False, True, True, False]
        error = master.write_multiple_coils(5, coil_values)
        if error == ModbusError.OK:
            print("Çoklu coil yazma başarılı")
        else:
            print(f"Çoklu coil yazma hatası: {error}")
            
        # Örnek 6: Çoklu register yazma
        register_values = [0x1111, 0x2222, 0x3333]
        error = master.write_multiple_registers(5, register_values)
        if error == ModbusError.OK:
            print("Çoklu register yazma başarılı")
        else:
            print(f"Çoklu register yazma hatası: {error}")
            
        # Değişiklikleri kontrol et
        print("\n=== DEĞİŞİKLİKLERİ KONTROL ET ===")
        error, updated_registers = master.read_holding_registers(0, 2)
        if error == ModbusError.OK:
            print("Güncel Register Değerleri:")
            for addr, value in enumerate(updated_registers):
                print(f"  Register {addr}: 0x{value:04X}")
                
    except Exception as e:
        print(f"Hata oluştu: {e}")
    
    finally:
        # Bağlantıyı kapat
        master.close()
        print("\nMaster bağlantısı kapatıldı")

if __name__ == "__main__":
    main()
