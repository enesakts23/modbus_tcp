#!/usr/bin/env python3
"""
BMS Slave Adres Test Aracı
Bu araç hangi adreslerde veri olduğunu gösterir
"""

from bms_register_map import BMSRegisters, BMSCoils, BMSDataConverter, BMSAddressCalculator

def test_addresses():
    print("🔍 BMS SLAVE ADRES REHBERİ")
    print("="*60)
    
    print("\n📊 ANA REGISTER'LAR (Function Code 03 - Read Holding Registers):")
    print(f"  SOC: {BMSRegisters.SOC_HIGH}-{BMSRegisters.SOC_LOW} (32-bit float)")
    print(f"  SOH: {BMSRegisters.SOH_HIGH}-{BMSRegisters.SOH_LOW} (32-bit float)")  
    print(f"  Total Voltage: {BMSRegisters.TOTAL_VOLTAGE_HIGH}-{BMSRegisters.TOTAL_VOLTAGE_LOW} (32-bit float)")
    print(f"  Current: {BMSRegisters.CURRENT_HIGH}-{BMSRegisters.CURRENT_LOW} (32-bit float)")
    print(f"  Max Temperature: {BMSRegisters.MAX_TEMPERATURE_HIGH}-{BMSRegisters.MAX_TEMPERATURE_LOW} (32-bit float)")
    
    print("\n🔋 HÜCRE VOLTAJLARI (Function Code 03):")
    try:
        addr1 = BMSAddressCalculator.get_cell_voltage_address(1, 1, 1)
        addr2 = BMSAddressCalculator.get_cell_voltage_address(1, 1, 2)
        print(f"  String-1, Paket-1, Hücre-1: {addr1}-{addr1+1} (32-bit float)")
        print(f"  String-1, Paket-1, Hücre-2: {addr2}-{addr2+1} (32-bit float)")
        print(f"  ... (toplam 4,992 hücre)")
    except Exception as e:
        print(f"  ❌ Hücre adresi hesaplama hatası: {e}")
    
    print("\n🌡️ SICAKLIK SENSÖRLERİ (Function Code 03):")
    try:
        temp_addr1 = BMSAddressCalculator.get_temperature_address(1, 1, 1, 1)
        temp_addr2 = BMSAddressCalculator.get_temperature_address(1, 1, 1, 2)
        print(f"  String-1, Paket-1, BMS-1, Sensör-1: {temp_addr1}-{temp_addr1+1} (32-bit float)")
        print(f"  String-1, Paket-1, BMS-1, Sensör-2: {temp_addr2}-{temp_addr2+1} (32-bit float)")
        print(f"  ... (toplam 2,304 sensör)")
    except Exception as e:
        print(f"  ❌ Sıcaklık adresi hesaplama hatası: {e}")
    
    print("\n🔧 COIL REGISTER'LAR (Function Code 03):")
    print(f"  Average Temperature: {BMSCoils.AVG_TEMP_HIGH}-{BMSCoils.AVG_TEMP_LOW} (32-bit float)")
    print(f"  Average Cell Voltage: {BMSCoils.AVG_CELLV_HIGH}-{BMSCoils.AVG_CELLV_LOW} (32-bit float)")
    print(f"  Pack Voltage: {BMSCoils.PACK_VOLT_HIGH}-{BMSCoils.PACK_VOLT_LOW} (32-bit float)")
    
    print("\n🎛️ COIL BİTLERİ (Function Code 01 - Read Coils):")
    print("  Adres 0-9: Test coil'leri (0,2,4,6,8 aktif)")
    
    print("\n⚠️ DİSCRETE INPUTS (Function Code 02 - Read Discrete Inputs):")
    print("  Adres 20000+: Alarm bitleri")
    
    print("\n" + "="*60)
    print("📋 MODBUS POLL AYARLARI:")
    print("="*60)
    print("💡 Temel Test için:")
    print("  Function Code: 03 (Read Holding Registers)")
    print("  Starting Address: 1000")
    print("  Quantity: 10")
    print("  Device ID: 1")
    print("  Connection: TCP/IP")
    print("  IP Address: [BMS_SLAVE_IP]")
    print("  Port: 1024")
    print("  Poll Rate: 1000ms")
    
    print("\n💡 Hücre Voltajları için:")
    print("  Function Code: 03")
    print("  Starting Address: 1010")
    print("  Quantity: 4 (2 hücre için)")
    
    print("\n💡 Coil Bitlerini test için:")
    print("  Function Code: 01 (Read Coils)")
    print("  Starting Address: 0")
    print("  Quantity: 10")
    
    print("\n💡 32-bit Float Değerleri Okumak için:")
    print("  - İki ardışık register'ı birlikte okuyun")
    print("  - High register (ilk) + Low register (ikinci)")
    print("  - IEEE 754 formatında decode edin")
    
    print("\n🔍 Test Örnekleri:")
    print("  SOC okumak için: Address=1000, Count=2")
    print("  İlk hücre voltajı için: Address=1010, Count=2") 
    print("  Average temp için: Address=30003, Count=2")

if __name__ == "__main__":
    test_addresses()
