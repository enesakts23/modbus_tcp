#!/usr/bin/env python3
"""
Modbus Poll değerlerini hızlı decode et
"""

import struct

def decode_modbus_values():
    print("🔍 MODBUS POLL DEĞERLERİNİ DECODE ET")
    print("="*50)
    
    # Şu anki değerleriniz
    values = {
        "SOC": (17064, 52436),  # 0x42A8, 0xCCD4 (unsigned)
        "SOH": (17093, 32768),  # 1002, 1003
        "Total Voltage": (17353, 39322),  # 1004, 1005 (unsigned)
        "Max Temp": (16876, 55382),  # 1006, 1007 (unsigned)
    }
    
    for name, (high, low) in values.items():
        try:
            # 32-bit float'a çevir
            bytes_data = high.to_bytes(2, 'big') + low.to_bytes(2, 'big')
            result = struct.unpack('>f', bytes_data)[0]
            print(f"{name:15}: {result:8.2f}")
        except Exception as e:
            print(f"{name:15}: HATA - {e}")

def hex_to_float_converter():
    print("\n" + "="*50)
    print("🔢 MANUEL CONVERTER")
    print("Modbus Poll'dan aldığınız değerleri girin:")
    print("Örnek: High=17064, Low=52436")
    
    try:
        high = int(input("\nHigh Register (decimal): "))
        low = int(input("Low Register (decimal): "))
        
        # Negatif değerleri unsigned'a çevir
        if low < 0:
            low = low + 65536
            
        bytes_data = high.to_bytes(2, 'big') + low.to_bytes(2, 'big')
        result = struct.unpack('>f', bytes_data)[0]
        
        print(f"\n✅ Sonuç: {result:.3f}")
        
        # Tahmin
        if 0 <= result <= 100:
            print(f"   → SOC/SOH: {result:.1f}%")
        elif 300 <= result <= 500:
            print(f"   → Voltaj: {result:.1f}V")
        elif -200 <= result <= 200:
            print(f"   → Akım: {result:.1f}A")
        elif 0 <= result <= 100:
            print(f"   → Sıcaklık: {result:.1f}°C")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    decode_modbus_values()
    hex_to_float_converter()
