#!/usr/bin/env python3
"""
Modbus Register Decoder - Hex değerleri gerçek değerlere çevirir
"""

import struct

def hex_to_float(high_hex, low_hex):
    """İki hex register'ı 32-bit float'a çevir"""
    try:
        # Hex string'leri integer'a çevir
        if isinstance(high_hex, str):
            high_reg = int(high_hex, 16)
        else:
            high_reg = high_hex
            
        if isinstance(low_hex, str):
            low_reg = int(low_hex, 16)
        else:
            low_reg = low_hex
            
        # 32-bit float'a çevir
        bytes_data = high_reg.to_bytes(2, 'big') + low_reg.to_bytes(2, 'big')
        return struct.unpack('>f', bytes_data)[0]
    except:
        return None

def decode_bms_values():
    print("🔢 MODBUS REGISTER DECODER")
    print("="*50)
    print("Modbus Poll'dan aldığınız hex değerleri buraya girin:")
    print("Örnek: 42B1 0000 → 88.5")
    print()
    
    while True:
        print("\n" + "-"*30)
        print("Çıkmak için 'q' yazın")
        
        # Kullanıcıdan veri al
        user_input = input("\nHex değerler (örn: 42B1 0000): ").strip()
        
        if user_input.lower() == 'q':
            break
            
        try:
            # Hex değerleri ayır
            parts = user_input.split()
            if len(parts) == 2:
                high_hex = parts[0]
                low_hex = parts[1]
                
                # Float'a çevir
                result = hex_to_float(high_hex, low_hex)
                
                if result is not None:
                    print(f"✅ Sonuç: {result:.2f}")
                    
                    # Tahmin et ne olabilir
                    if 0 <= result <= 100:
                        print(f"   → Muhtemelen: SOC ({result:.1f}%) veya SOH ({result:.1f}%)")
                    elif 300 <= result <= 500:
                        print(f"   → Muhtemelen: Voltaj ({result:.1f}V)")
                    elif -200 <= result <= 200:
                        print(f"   → Muhtemelen: Akım ({result:.1f}A)")
                    elif 0 <= result <= 100:
                        print(f"   → Muhtemelen: Sıcaklık ({result:.1f}°C)")
                    elif 3 <= result <= 5:
                        print(f"   → Muhtemelen: Hücre Voltajı ({result:.3f}V)")
                        
                else:
                    print("❌ Geçersiz hex değer")
                    
            else:
                print("❌ İki hex değer girin (örn: 42B1 0000)")
                
        except Exception as e:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    print("📋 BMS REGISTER ADRESLERİ:")
    print("  SOC: 1000-1001")
    print("  Current: 1008-1009") 
    print("  Total Voltage: 1004-1005")
    print("  İlk Hücre: 1010-1011")
    print("  Average Temp: 30003-30004")
    print()
    
    decode_bms_values()
