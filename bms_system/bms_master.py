import time
import random
from modbus import ModbusMaster
from bms_register_map import BMSAddressCalculator, BMSRegisters, BMSDataConverter, BMSCoils

class MegaBMSMaster:
    
    def __init__(self, host="127.0.0.1", port=1024):
        self.master = ModbusMaster()
        self.host = host
        self.port = port
        
    def connect(self):
        try:
            if self.master.connect(self.host, self.port):
                print(f"✅ MEGA BMS Slave'e bağlanıldı ({self.host}:{self.port})")
                return True
            else:
                print(f"❌ Bağlantı kurulamadı ({self.host}:{self.port})")
                return False
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        self.master.close()
        print("📴 MEGA BMS bağlantısı kapatıldı")
    
    def read_main_parameters(self):
        try:
            print("\n📊 ANA BMS PARAMETRELERİ:")
            print("-" * 50)
            
            # SOC oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSRegisters.SOC_HIGH, 2)
            if error.value == 0 and response:
                soc = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🔋 SOC (Şarj Durumu): {soc:.2f}%")
            
            # SOH oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSRegisters.SOH_HIGH, 2)
            if error.value == 0 and response:
                soh = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"� SOH (Sağlık Durumu): {soh:.2f}%")
            
            # Total Voltage oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSRegisters.TOTAL_VOLTAGE_HIGH, 2)
            if error.value == 0 and response:
                total_voltage = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"⚡ Toplam Voltaj: {total_voltage:.2f}V")
            
            # Max Temperature oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSRegisters.MAX_TEMPERATURE_HIGH, 2)
            if error.value == 0 and response:
                temp = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🌡️ Max Sıcaklık: {temp:.2f}°C")
            
            # Current oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSRegisters.CURRENT_HIGH, 2)
            if error.value == 0 and response:
                current = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🔌 Akım: {current:.2f}A")
                
                return {
                    'soc': soc,
                    'soh': soh,
                    'voltage': total_voltage,
                    'temperature': temp,
                    'current': current
                }
            else:
                print(f"❌ Ana parametre okuma hatası: {error}")
            
        except Exception as e:
            print(f"❌ Ana parametre okuma hatası: {e}")
        
        return None
    
    def read_sample_cells(self, sample_count=20):
        try:
            print(f"\n🔋 ÖRNEK HÜCRE VOLTAJLARI ({sample_count} adet) - 32-bit float:")
            print("-" * 70)
            
            cells_read = 0
            for string in range(1, 13):
                if cells_read >= sample_count:
                    break
                    
                for packet in range(1, 5):
                    if cells_read >= sample_count:
                        break
                        
                    for cell in range(1, min(11, 105)):
                        if cells_read >= sample_count:
                            break
                            
                        try:
                            addr = BMSAddressCalculator.get_cell_voltage_address(string, packet, cell)
                            # 32-bit float için 2 register oku
                            error, response = self.master.read_holding_registers(addr, 2)
                            
                            if error.value == 0 and response:
                                voltage_v = BMSDataConverter.registers_to_float(response[0], response[1])
                                
                                print(f"📍 S{string:2d}-P{packet}-C{cell:3d}: {voltage_v:.4f}V (addr: {addr}-{addr+1})")
                                cells_read += 1
                                
                        except Exception as e:
                            print(f"❌ Hücre okuma hatası S{string}-P{packet}-C{cell}: {e}")
                            
            print(f"\n✅ {cells_read} hücre voltajı okundu")
            
        except Exception as e:
            print(f"❌ Hücre voltaj okuma hatası: {e}")
    
    def read_sample_temperatures(self, sample_count=20):
        try:
            print(f"\n🌡️ ÖRNEK SICAKLIK SENSÖRLERİ ({sample_count} adet) - 32-bit float:")
            print("-" * 70)
            
            temps_read = 0
            for string in range(1, 13):
                if temps_read >= sample_count:
                    break
                    
                for packet in range(1, 5):
                    if temps_read >= sample_count:
                        break
                        
                    for bms in range(1, 7):
                        if temps_read >= sample_count:
                            break
                            
                        for sensor in range(1, min(4, 9)):
                            if temps_read >= sample_count:
                                break
                                
                            try:
                                addr = BMSAddressCalculator.get_temperature_address(string, packet, bms, sensor)
                                # 32-bit float için 2 register oku
                                error, response = self.master.read_holding_registers(addr, 2)
                                
                                if error.value == 0 and response:
                                    temp_c = BMSDataConverter.registers_to_float(response[0], response[1])
                                    
                                    print(f"🌡️ S{string:2d}-P{packet}-B{bms}-T{sensor}: {temp_c:.2f}°C (addr: {addr}-{addr+1})")
                                    temps_read += 1
                                    
                            except Exception as e:
                                print(f"❌ Sıcaklık okuma hatası S{string}-P{packet}-B{bms}-T{sensor}: {e}")
                                
            print(f"\n✅ {temps_read} sıcaklık sensörü okundu")
            
        except Exception as e:
            print(f"❌ Sıcaklık okuma hatası: {e}")
    
    def read_string_summary(self, string_number):
        try:
            print(f"\n📋 STRING-{string_number} ÖZETİ:")
            print("-" * 50)
            
            total_voltage = 0
            cell_count = 0
            min_voltage = float('inf')
            max_voltage = 0
            temp_total = 0
            temp_count = 0
            
            for packet in range(1, 5):
                print(f"\n📦 Paket {packet}:")
                
                for cell in range(1, 11):
                    try:
                        addr = BMSAddressCalculator.get_cell_voltage_address(string_number, packet, cell)
                        error, response = self.master.read_holding_registers(addr, 1)
                        
                        if error.value == 0 and response:
                            voltage_mv = response[0]
                            voltage_v = voltage_mv / 1000.0
                            
                            total_voltage += voltage_v
                            cell_count += 1
                            min_voltage = min(min_voltage, voltage_v)
                            max_voltage = max(max_voltage, voltage_v)
                            
                            if cell <= 5:
                                print(f"  🔋 Hücre {cell:3d}: {voltage_v:.3f}V")
                            
                    except Exception as e:
                        print(f"  ❌ Hücre {cell} okuma hatası: {e}")
                
                for bms in range(1, 3):
                    for sensor in range(1, 3):
                        try:
                            addr = BMSAddressCalculator.get_temp_sensor_address(string_number, packet, bms, sensor)
                            error, response = self.master.read_holding_registers(addr, 1)
                            
                            if error.value == 0 and response:
                                temp_raw = response[0]
                                temp_c = temp_raw - 40
                                
                                temp_total += temp_c
                                temp_count += 1
                                
                                print(f"  🌡️ BMS{bms}-T{sensor}: {temp_c}°C")
                                
                        except Exception as e:
                            print(f"  ❌ Sıcaklık BMS{bms}-T{sensor} okuma hatası: {e}")
            
            if cell_count > 0:
                avg_voltage = total_voltage / cell_count
                print(f"\n📊 STRING-{string_number} İSTATİSTİKLERİ:")
                print(f"  📈 Ortalama Voltaj: {avg_voltage:.3f}V")
                print(f"  📉 Min Voltaj: {min_voltage:.3f}V")
                print(f"  📈 Max Voltaj: {max_voltage:.3f}V")
                print(f"  🔋 Okunan Hücre: {cell_count}")
                
            if temp_count > 0:
                avg_temp = temp_total / temp_count
                print(f"  🌡️ Ortalama Sıcaklık: {avg_temp:.1f}°C")
                print(f"  🌡️ Okunan Sensör: {temp_count}")
                
        except Exception as e:
            print(f"❌ String özet okuma hatası: {e}")
    
    def read_alarms_and_status(self):
        try:
            print("\n📊 SİSTEM DURUMU:")
            print("-" * 30)
            print("⚠️ Alarm sistemi kaldırıldı")
            
        except Exception as e:
            print(f"❌ Sistem durumu okuma hatası: {e}")
    
    def read_coil_data(self):
        try:
            print("\n🔧 COIL VERİLERİ (32-bit float format):")
            print("-" * 50)
            
            # AVG_TEMP oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSCoils.AVG_TEMP_HIGH, 2)
            if error.value == 0 and response:
                avg_temp = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🌡️ AVG_TEMP: {avg_temp:.2f}°C")
            
            # AVG_CELLV oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSCoils.AVG_CELLV_HIGH, 2)
            if error.value == 0 and response:
                avg_cellv = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"🔋 AVG_CELLV: {avg_cellv:.3f}V")
            
            # PACK_VOLT oku (32-bit float, 2 register)
            error, response = self.master.read_holding_registers(BMSCoils.PACK_VOLT_HIGH, 2)
            if error.value == 0 and response:
                pack_volt = BMSDataConverter.registers_to_float(response[0], response[1])
                print(f"⚡ PACK_VOLT: {pack_volt:.2f}V")
                
        except Exception as e:
            print(f"❌ Coil okuma hatası: {e}")
    
    def run_continuous_main_monitoring(self, interval=3):
        print(f"\n🔄 SÜREKLI ANA PARAMETRE İZLEME (Her {interval} saniye):")
        print("CTRL+C ile durdurun")
        print("=" * 80)
        
        try:
            while True:
                print(f"\n⏰ {time.strftime('%H:%M:%S')} - ANA PARAMETRELER:")
                print("-" * 50)
                
                main_data = self.read_main_parameters()
                
                if main_data:
                    power = main_data['voltage'] * abs(main_data['current']) / 1000
                    
                    print(f"📊 SOC: {main_data['soc']:3d}% | SOH: {main_data['soh']:3d}% | V: {main_data['voltage']:6.1f}V | T: {main_data['temperature']:3d}°C | I: {main_data['current']:6.1f}A | P: {power:5.1f}kW")
                
                print("-" * 80)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Sürekli ana parametre izleme durduruldu")

def main():
    print("🚀 MEGA BMS MASTER BAŞLATILIYOR")
    print("=" * 80)
    print("📊 Sistem Kapasitesi:")
    print("  🔋 Toplam Hücre: 4,992 (12 String × 4 Paket × 104 Hücre)")
    print("  🌡️ Toplam Sensör: 2,304 (12 String × 4 Paket × 6 BMS × 8 Sensör)")
    print("=" * 80)
    
    master = MegaBMSMaster()
    
    if not master.connect():
        print("❌ MEGA BMS Slave'e bağlanılamadı!")
        print("🔍 Kontrol listesi:")
        print("  - BMS Slave çalışıyor mu? (python bms_slave.py)")
        print("  - Port 1024 açık mı?")
        return
    
    try:
        while True:
            print("\n" + "=" * 80)
            print("🎛️ MEGA BMS MASTER MENÜSÜ:")
            print("=" * 80)
            print("📊 ANA SENARYOLAR:")
            print("1️⃣  Ana Parametreler (SOC, SOH, Voltaj, Sıcaklık, Akım)")
            print("2️⃣  Kapsamlı Sistem Okuma (Tüm veriler)")
            print("")
            print("🔧 DETAYLI OKUMA SEÇENEKLERİ:")
            print("3️⃣  Örnek hücre voltajları (seçilebilir sayıda)")
            print("4️⃣  Örnek sıcaklık sensörleri (seçilebilir sayıda)")
            print("5️⃣  String detay analizi (1-12 arası)")
            print("6️⃣  Alarm ve durum bilgileri")
            print("7️⃣  Coil verileri")
            print("")
            print("⚡ İZLEME MODLARI:")
            print("8️⃣  Sürekli ana parametre izleme")
            print("")
            print("0️⃣  Çıkış")
            print("-" * 80)
            
            choice = input("🎯 Seçiminizi yapın (0-8): ").strip()
            
            if choice == "1":
                print("\n🎯 ANA PARAMETRELER SENARYOSU")
                print("=" * 60)
                main_data = master.read_main_parameters()
                if main_data:
                    print(f"\n📈 ÖZET:")
                    print(f"  ⚡ Sistem Voltajı: {main_data['voltage']:.1f}V")
                    print(f"  🔋 Batarya Durumu: SOC {main_data['soc']}% | SOH {main_data['soh']}%")
                    print(f"  🌡️ Sıcaklık: {main_data['temperature']}°C")
                    print(f"  🔌 Akım: {main_data['current']:.1f}A {'(Şarj)' if main_data['current'] > 0 else '(Deşarj)' if main_data['current'] < 0 else '(Boşta)'}")
                    
                    power = main_data['voltage'] * abs(main_data['current']) / 1000
                    print(f"  ⚡ Anlık Güç: {power:.1f}kW")
                
            elif choice == "2":
                print("\n🚀 KAPSAMLI SİSTEM OKUMA SENARYOSU")
                print("=" * 80)
                
                master.read_main_parameters()
                
                print(f"\n📊 SİSTEM GENELİ ÖRNEKLEME:")
                master.read_sample_cells(50)
                master.read_sample_temperatures(30)
                
                for string_no in [1, 6, 12]:
                    master.read_string_summary(string_no)
                
                master.read_alarms_and_status()
                
                print("\n✅ Kapsamlı sistem analizi tamamlandı!")
                
            elif choice == "3":
                try:
                    count = int(input("📍 Kaç hücre voltajı okunacak? [20]: ") or "20")
                    master.read_sample_cells(count)
                except ValueError:
                    master.read_sample_cells(20)
                
            elif choice == "4":
                try:
                    count = int(input("🌡️ Kaç sıcaklık sensörü okunacak? [20]: ") or "20")
                    master.read_sample_temperatures(count)
                except ValueError:
                    master.read_sample_temperatures(20)
                
            elif choice == "5":
                try:
                    string_num = int(input("📍 String numarası (1-12): "))
                    if 1 <= string_num <= 12:
                        master.read_string_summary(string_num)
                    else:
                        print("❌ Geçersiz string numarası! (1-12)")
                except ValueError:
                    print("❌ Geçersiz numara!")
                    
            elif choice == "6":
                master.read_alarms_and_status()
                
            elif choice == "7":
                master.read_coil_data()
                
            elif choice == "8":
                print("\n🔄 SÜREKLI ANA PARAMETRE İZLEME")
                try:
                    interval = int(input("⏰ İzleme aralığı (saniye) [3]: ") or "3")
                    master.run_continuous_main_monitoring(interval)
                except ValueError:
                    master.run_continuous_main_monitoring(3)
                    
            elif choice == "0":
                print("👋 MEGA BMS Master kapatılıyor...")
                break
                
            else:
                print("❌ Geçersiz seçim!")
            
            input("\n⏳ Devam etmek için ENTER'a basın...")
            
    except KeyboardInterrupt:
        print("\n🛑 Program sonlandırıldı")
        
    finally:
        master.disconnect()

if __name__ == "__main__":
    main()
