import sys
import os
import time
import random

# Relative import için path ekleme
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modbus import ModbusMaster
from bms_system.bms_register_map import BMSAddressCalculator, BMSRegisters, BMSDataConverter

class MegaBMSMaster:

    def __init__(self, host="127.0.0.1", port=1024):
        self.master = ModbusMaster()
        self.host = hos                
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
                    print("❌ Geçersiz numara!")= port
        
    def connect(self):
        """MEGA BMS Slave'e bağlan"""
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
        """Bağlantıyı kapat"""
        self.master.close()
        print("📴 MEGA BMS bağlantısı kapatıldı")
    
    def read_main_parameters(self):
        """Ana BMS parametrelerini oku"""
        try:
            print("\n� ANA BMS PARAMETRELERİ:")
            print("-" * 50)
            
            # Ana veriler
            response = self.master.read_holding_registers(BMSRegisters.SOC, 5)
            if response:
                soc = response[0]
                soh = response[1]
                total_voltage = response[2] / 10.0
                temp = response[3] - 40
                current = BMSDataConverter.raw_to_current(response[4])
                
                print(f"🔋 SOC (Şarj Durumu): {soc}%")
                print(f"� SOH (Sağlık Durumu): {soh}%")
                print(f"⚡ Toplam Voltaj: {total_voltage:.1f}V")
                print(f"🌡️ Ortalama Sıcaklık: {temp}°C")
                print(f"🔌 Akım: {current:.1f}A")
                
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
    
    def read_sample_cells(self, sample_count=20):
        """Örnek hücre voltajlarını oku"""
        try:
            print(f"\n🔋 ÖRNEK HÜCRE VOLTAJLARI ({sample_count} adet):")
            print("-" * 60)
            
            cells_read = 0
            for string in range(1, 13):  # 12 string
                if cells_read >= sample_count:
                    break
                    
                for packet in range(1, 5):  # 4 paket
                    if cells_read >= sample_count:
                        break
                        
                    for cell in range(1, min(11, 105)):  # İlk 10 hücre
                        if cells_read >= sample_count:
                            break
                            
                        try:
                            addr = BMSAddressCalculator.get_cell_voltage_address(string, packet, cell)
                            response = self.master.read_holding_registers(addr, 1)
                            
                            if response:
                                voltage_mv = response[0]
                                voltage_v = voltage_mv / 1000.0
                                
                                print(f"� S{string:2d}-P{packet}-C{cell:3d}: {voltage_v:.3f}V (addr: {addr})")
                                cells_read += 1
                                
                        except Exception as e:
                            print(f"❌ Hücre okuma hatası S{string}-P{packet}-C{cell}: {e}")
                            
            print(f"\n✅ {cells_read} hücre voltajı okundu")
            
        except Exception as e:
            print(f"❌ Hücre voltaj okuma hatası: {e}")
    
    def read_sample_temperatures(self, sample_count=20):
        """Örnek sıcaklık sensörlerini oku"""
        try:
            print(f"\n🌡️ ÖRNEK SICAKLIK SENSÖRLERİ ({sample_count} adet):")
            print("-" * 60)
            
            temps_read = 0
            for string in range(1, 13):  # 12 string
                if temps_read >= sample_count:
                    break
                    
                for packet in range(1, 5):  # 4 paket
                    if temps_read >= sample_count:
                        break
                        
                    for bms in range(1, 7):  # 6 BMS
                        if temps_read >= sample_count:
                            break
                            
                        for sensor in range(1, 9):  # 8 sensör
                            if temps_read >= sample_count:
                                break
                                
                            try:
                                addr = BMSAddressCalculator.get_temp_sensor_address(string, packet, bms, sensor)
                                response = self.master.read_holding_registers(addr, 1)
                                
                                if response:
                                    temp_raw = response[0]
                                    temp_c = temp_raw - 40
                                    
                                    print(f"📍 S{string:2d}-P{packet}-B{bms}-T{sensor}: {temp_c:3d}°C (addr: {addr})")
                                    temps_read += 1
                                    
                            except Exception as e:
                                print(f"❌ Sıcaklık okuma hatası S{string}-P{packet}-B{bms}-T{sensor}: {e}")
                                
            print(f"\n✅ {temps_read} sıcaklık sensörü okundu")
            
        except Exception as e:
            print(f"❌ Sıcaklık okuma hatası: {e}")
    
    def read_string_summary(self, string_number):
        """Belirli bir string'in özet bilgilerini oku"""
        try:
            print(f"\n📋 STRING-{string_number} ÖZETİ:")
            print("-" * 50)
            
            total_voltage = 0
            cell_count = 0
            min_voltage = float('inf')
            max_voltage = 0
            temp_total = 0
            temp_count = 0
            
            # String'deki tüm paketleri oku
            for packet in range(1, 5):  # 4 paket
                print(f"\n📦 Paket {packet}:")
                
                # İlk 10 hücreyi oku (demo için)
                for cell in range(1, 11):
                    try:
                        addr = BMSAddressCalculator.get_cell_voltage_address(string_number, packet, cell)
                        response = self.master.read_holding_registers(addr, 1)
                        
                        if response:
                            voltage_mv = response[0]
                            voltage_v = voltage_mv / 1000.0
                            
                            total_voltage += voltage_v
                            cell_count += 1
                            min_voltage = min(min_voltage, voltage_v)
                            max_voltage = max(max_voltage, voltage_v)
                            
                            if cell <= 5:  # İlk 5 hücreyi göster
                                print(f"  🔋 Hücre {cell:3d}: {voltage_v:.3f}V")
                            
                    except Exception as e:
                        print(f"  ❌ Hücre {cell} okuma hatası: {e}")
                
                # İlk 4 sıcaklık sensörünü oku (demo için)
                for bms in range(1, 3):  # İlk 2 BMS
                    for sensor in range(1, 3):  # İlk 2 sensör
                        try:
                            addr = BMSAddressCalculator.get_temp_sensor_address(string_number, packet, bms, sensor)
                            response = self.master.read_holding_registers(addr, 1)
                            
                            if response:
                                temp_raw = response[0]
                                temp_c = temp_raw - 40
                                
                                temp_total += temp_c
                                temp_count += 1
                                
                                print(f"  🌡️ BMS{bms}-T{sensor}: {temp_c}°C")
                                
                        except Exception as e:
                            print(f"  ❌ Sıcaklık BMS{bms}-T{sensor} okuma hatası: {e}")
            
            # Özet istatistikler
            if cell_count > 0:
                avg_voltage = total_voltage / cell_count
                print(f"\n📊 STRING-{string_number} İSTATİSTİKLERİ:")
                print(f"  📈 Ortalama Voltaj: {avg_voltage:.3f}V")
                print(f"  📉 Min Voltaj: {min_voltage:.3f}V")
                print(f"  � Max Voltaj: {max_voltage:.3f}V")
                print(f"  🔋 Okunan Hücre: {cell_count}")
                
            if temp_count > 0:
                avg_temp = temp_total / temp_count
                print(f"  🌡️ Ortalama Sıcaklık: {avg_temp:.1f}°C")
                print(f"  🌡️ Okunan Sensör: {temp_count}")
                
        except Exception as e:
            print(f"❌ String özet okuma hatası: {e}")
    
    def read_alarms_and_status(self):
        """Alarm ve durum bilgilerini oku"""
        try:
            print("\n⚠️ ALARM VE DURUM BİLGİLERİ:")
            print("-" * 50)
            
            # Alarmları oku
            response = self.master.read_holding_registers(20000, 16)
            if response:
                alarms = [
                    "Aşırı Voltaj", "Düşük Voltaj", "Aşırı Sıcaklık", "Düşük Sıcaklık",
                    "Aşırı Akım", "İletişim Hatası", "Balans Hatası", "Fan Hatası",
                    "İzolatör Hatası", "BMS Hatası", "Fuse Hatası", "Kontaktör Hatası",
                    "SOC Düşük", "SOH Düşük", "Kalibrasyon Hatası", "Genel Hata"
                ]
                
                active_alarms = []
                for i, alarm in enumerate(alarms):
                    if i < len(response) and response[i]:
                        active_alarms.append(f"🚨 {alarm}")
                
                if active_alarms:
                    for alarm in active_alarms:
                        print(alarm)
                else:
                    print("✅ Aktif alarm yok")
            
            # Durum bilgilerini oku
            response = self.master.read_holding_registers(20100, 6)
            if response:
                print(f"\n📊 DURUM BİLGİLERİ:")
                print(f"  🔄 Sistem Durumu: {response[0]}")
                print(f"  🔋 Şarj Durumu: {response[1]}")
                print(f"  🌡️ Termal Durum: {response[2]}")
                print(f"  ⚡ Güç Durumu: {response[3]}")
                print(f"  🔧 Bakım Durumu: {response[4]}")
                print(f"  📡 İletişim Durumu: {response[5]}")
                
        except Exception as e:
            print(f"❌ Alarm/durum okuma hatası: {e}")
    
    def run_continuous_monitoring(self, interval=5):
        """Sürekli izleme modu"""
        print(f"\n🔄 SÜREKLI İZLEME MODU (Her {interval} saniye):")
        print("CTRL+C ile durdurun")
        print("=" * 80)
        
        try:
            while True:
                print(f"\n⏰ {time.strftime('%H:%M:%S')} - MEGA BMS Durumu:")
                
                # Ana parametreleri oku
                main_params = self.read_main_parameters()
                
                # Rastgele bir string'i detaylandır
                random_string = random.randint(1, 12)
                print(f"\n🎯 Rastgele String-{random_string} detayı:")
                
                # String'den 5 hücre oku
                for packet in range(1, 3):  # İlk 2 paket
                    for cell in range(1, 4):  # İlk 3 hücre
                        try:
                            addr = BMSAddressCalculator.get_cell_voltage_address(random_string, packet, cell)
                            response = self.master.read_holding_registers(addr, 1)
                            
                            if response:
                                voltage_v = response[0] / 1000.0
                                print(f"  🔋 S{random_string}-P{packet}-C{cell}: {voltage_v:.3f}V")
                                
                        except Exception as e:
                            print(f"  ❌ Hücre okuma hatası: {e}")
                
                print("\n" + "-" * 80)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Sürekli izleme durduruldu")
    
    def run_continuous_main_monitoring(self, interval=3):
        """Sürekli ana parametre izleme modu"""
        print(f"\n🔄 SÜREKLI ANA PARAMETRE İZLEME (Her {interval} saniye):")
        print("CTRL+C ile durdurun")
        print("=" * 80)
        
        try:
            while True:
                print(f"\n⏰ {time.strftime('%H:%M:%S')} - ANA PARAMETRELER:")
                print("-" * 50)
                
                # Ana parametreleri oku ve görüntüle
                main_data = self.read_main_parameters()
                
                if main_data:
                    # Güç hesapla
                    power = main_data['voltage'] * abs(main_data['current']) / 1000  # kW
                    
                    # Kompakt görünüm
                    print(f"📊 SOC: {main_data['soc']:3d}% | SOH: {main_data['soh']:3d}% | V: {main_data['voltage']:6.1f}V | T: {main_data['temperature']:3d}°C | I: {main_data['current']:6.1f}A | P: {power:5.1f}kW")
                
                print("-" * 80)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Sürekli ana parametre izleme durduruldu")

def main():
    """Ana fonksiyon - MEGA BMS Master testi"""
    print("� MEGA BMS MASTER BAŞLATILIYOR")
    print("=" * 80)
    print("📊 Sistem Kapasitesi:")
    print("  🔋 Toplam Hücre: 4,992 (12 String × 4 Paket × 104 Hücre)")
    print("  🌡️ Toplam Sensör: 2,304 (12 String × 4 Paket × 6 BMS × 8 Sensör)")
    print("=" * 80)
    
    master = MegaBMSMaster()
    
    if not master.connect():
        print("❌ MEGA BMS Slave'e bağlanılamadı!")
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
            print("")
            print("⚡ İZLEME MODLARI:")
            print("7️⃣  Sürekli ana parametre izleme")
            print("8️⃣  Sürekli kapsamlı izleme")
            print("")
            print("0️⃣  Çıkış")
            print("-" * 80)
            
            choice = input("🎯 Seçiminizi yapın (0-8): ").strip()
            
            if choice == "1":
                # ANA PARAMETRELER SENARYOSU
                print("\n🎯 ANA PARAMETRELER SENARYOSU")
                print("=" * 60)
                main_data = master.read_main_parameters()
                if main_data:
                    print(f"\n📈 ÖZET:")
                    print(f"  ⚡ Sistem Voltajı: {main_data['voltage']:.1f}V")
                    print(f"  🔋 Batarya Durumu: SOC {main_data['soc']}% | SOH {main_data['soh']}%")
                    print(f"  🌡️ Sıcaklık: {main_data['temperature']}°C")
                    print(f"  🔌 Akım: {main_data['current']:.1f}A {'(Şarj)' if main_data['current'] > 0 else '(Deşarj)' if main_data['current'] < 0 else '(Boşta)'}")
                    
                    # Güç hesapla
                    power = main_data['voltage'] * abs(main_data['current']) / 1000  # kW
                    print(f"  ⚡ Anlık Güç: {power:.1f}kW")
                
            elif choice == "2":
                # KAPSAMLI SİSTEM OKUMA SENARYOSU
                print("\n🚀 KAPSAMLI SİSTEM OKUMA SENARYOSU")
                print("=" * 80)
                
                # Ana parametreler
                master.read_main_parameters()
                
                # Sistem geneli örnekleme
                print(f"\n📊 SİSTEM GENELİ ÖRNEKLEME:")
                master.read_sample_cells(50)  # Daha fazla hücre örneği
                master.read_sample_temperatures(30)  # Daha fazla sıcaklık örneği
                
                # İlk 3 string'in detayı
                for string_no in [1, 6, 12]:  # Başlangıç, orta, son
                    master.read_string_summary(string_no)
                
                # Alarm ve durum
                master.read_alarms_and_status()
                
                print("\n✅ Kapsamlı sistem analizi tamamlandı!")
                
            elif choice == "3":
                try:
                    count = int(input("📍 Kaç hücre voltajı okunacak? [20]: ") or "20")
                    master.read_sample_cells(count)
                except ValueError:
                    master.read_sample_cells(20)
                
            elif choice == "3":
                master.read_sample_temperatures(20)
                
            elif choice == "4":
                try:
                    string_num = int(input("� String numarası (1-12): "))
                    if 1 <= string_num <= 12:
                        master.read_string_summary(string_num)
                    else:
                        print("❌ Geçersiz string numarası! (1-12)")
                except ValueError:
                    print("❌ Geçersiz numara!")
                    
            elif choice == "5":
                master.read_alarms_and_status()
                
            elif choice == "6":
                try:
                    interval = int(input("⏰ İzleme aralığı (saniye) [5]: ") or "5")
                    master.run_continuous_monitoring(interval)
                except ValueError:
                    master.run_continuous_monitoring(5)
                    
            elif choice == "7":
                print("\n🚀 KAPSAMLI TEST BAŞLATILIYOR...")
                print("=" * 80)
                
                master.read_main_parameters()
                master.read_sample_cells(10)
                master.read_sample_temperatures(10)
                master.read_string_summary(1)
                master.read_alarms_and_status()
                
                print("\n✅ Kapsamlı test tamamlandı!")
                
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
