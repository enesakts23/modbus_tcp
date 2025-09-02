import time
import random
from modbus import ModbusMaster
from bms_register_map import BMSAddressCalculator, BMSRegisters, BMSDataConverter, BMSCoils

class NuvelBMSMaster:
    
    def __init__(self, host="127.0.0.1", port=1024):
        self.master = ModbusMaster()
        self.host = host
        self.port = port
        
    def connect(self):
        try:
            if self.master.connect(self.host, self.port):
                print(f"✅ NUVEL BMS Slave'e bağlanıldı ({self.host}:{self.port})")
                return True
            else:
                print(f"❌ Bağlantı kurulamadı ({self.host}:{self.port})")
                return False
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        self.master.close()
        print("📴 NUVEL BMS bağlantısı kapatıldı")
    
    def read_main_parameters(self):
        try:
            print("\n📊 ANA BMS PARAMETRELERİ:")
            print("-" * 50)
            
            soc = 0
            soh = 0
            total_voltage = 0
            temp = 0
            current = 0
            
            error, response = self.master.read_holding_registers(BMSRegisters.SOC_HIGH, 2)
            if error.value == 0 and response:
                soc = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🔋 SOC (Şarj Durumu): {soc:.2f}%")
            
            error, response = self.master.read_holding_registers(BMSRegisters.SOH_HIGH, 2)
            if error.value == 0 and response:
                soh = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"💚 SOH (Sağlık Durumu): {soh:.2f}%")
            
            error, response = self.master.read_holding_registers(BMSRegisters.TOTAL_VOLTAGE_HIGH, 2)
            if error.value == 0 and response:
                total_voltage = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"⚡ Toplam Voltaj: {total_voltage:.2f}V")
            
            error, response = self.master.read_holding_registers(BMSRegisters.MAX_TEMPERATURE_HIGH, 2)
            if error.value == 0 and response:
                temp = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🌡️ Max Sıcaklık: {temp:.2f}°C")
            
            error, response = self.master.read_holding_registers(BMSRegisters.CURRENT_HIGH, 2)
            if error.value == 0 and response:
                current = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🔌 Akım: {current:.2f}A")
                
            power = total_voltage * abs(current) / 1000
            print(f"⚡ Anlık Güç: {power:.1f}kW")
            
            return {
                'soc': soc,
                'soh': soh,
                'voltage': total_voltage,
                'temperature': temp,
                'current': current
            }
            
        except Exception as e:
            print(f"❌ Ana parametre okuma hatası: {e}")
        
        return None

def main():
    print("🚀 NUVEL BMS MASTER BAŞLATILIYOR")
    print("=" * 80)
    print("📊 Sistem Kapasitesi:")
    print("  🔋 Toplam Hücre: 4,992 (12 String × 4 Paket × 104 Hücre)")
    print("  🌡️ Toplam Sensör: 2,304 (12 String × 4 Paket × 6 BMS × 8 Sensör)")
    print("=" * 80)
    
    master = NuvelBMSMaster()
    
    if not master.connect():
        print("❌ NUVEL BMS Slave'e bağlanılamadı!")
        print("🔍 Kontrol listesi:")
        print("  - BMS Slave çalışıyor mu? (python bms_slave.py)")
        print("  - Port 1024 açık mı?")
        return
    
    print(f"\n🔄 ANA PARAMETRELER OTOMATİK İZLEME (Her 10 saniye)")
    print("CTRL+C ile durdurun")
    print("=" * 80)
    
    try:
        while True:
            print(f"\n⏰ {time.strftime('%H:%M:%S')} - ANA PARAMETRELER:")
            print("-" * 50)
            
            main_data = master.read_main_parameters()
            
            if main_data:
                print(f"📊 ÖZET: SOC {main_data['soc']:.1f}% | SOH {main_data['soh']:.1f}% | V {main_data['voltage']:.1f}V | T {main_data['temperature']:.1f}°C | I {main_data['current']:.1f}A")
            
            print("-" * 80)
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Ana parametre izleme durduruldu")
    finally:
        master.disconnect()

if __name__ == "__main__":
    main()