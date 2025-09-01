#!/usr/bin/env python3
"""
🔥 SAHTE CAN FD MESAJ SİMÜLATÖRÜ
================================================================================
Bu script, BMS sistemine sahte CAN FD mesajları göndererek 
gerçekçi hücre voltajları, sıcaklıklar, SOC, SOH, akım gibi 
BMS verilerini simüle eder.

Referans: balanslamamain.py ve temperature_page.py

KULLANIM:
python3 fake_can_simulator.py
================================================================================
"""

import time
import random
import struct
import threading
import sys
from datetime import datetime
import socket

class CANMessageSimulator:
    def __init__(self):
        self.running = False
        self.update_interval = 2.0  # 2 saniyede bir güncelle
        
        # BMS Sistem Yapısı
        self.TOTAL_STRINGS = 12
        self.PACKETS_PER_STRING = 4  
        self.BMS_PER_PACKET = 6
        self.CELLS_PER_BMS = [18, 18, 18, 18, 18, 14]  # BMS 1-5: 18 hücre, BMS 6: 14 hücre
        self.TEMPS_PER_BMS = 7  # Her BMS'te 7 sıcaklık sensörü
        
        # Simülasyon Verileri
        self.cell_voltages = {}  # {(string, packet, global_cell): voltage}
        self.temperatures = {}   # {(string, packet, global_temp): celsius}
        self.soc_values = {}     # {(string, packet): soc_percent}
        self.soh_values = {}     # {(string, packet): soh_percent}
        self.currents = {}       # {(string, packet): current_amps}
        self.pack_voltages = {}  # {(string, packet): total_voltage}
        
        # Başlangıç değerlerini oluştur
        self.initialize_fake_data()
        
        print("🚀 SAHTE CAN FD SİMÜLATÖRÜ BAŞLATILIYOR")
        print("=" * 80)
        print(f"📊 Sistem Kapasitesi:")
        print(f"  🔋 Toplam String: {self.TOTAL_STRINGS}")
        print(f"  📦 String başına Paket: {self.PACKETS_PER_STRING}")
        print(f"  🔧 Paket başına BMS: {self.BMS_PER_PACKET}")
        print(f"  ⚡ Toplam Hücre: {self.calculate_total_cells()}")
        print(f"  🌡️ Toplam Sıcaklık Sensörü: {self.calculate_total_temps()}")
        print("=" * 80)

    def calculate_total_cells(self):
        """Toplam hücre sayısını hesapla"""
        return self.TOTAL_STRINGS * self.PACKETS_PER_STRING * sum(self.CELLS_PER_BMS)

    def calculate_total_temps(self):
        """Toplam sıcaklık sensörü sayısını hesapla"""
        return self.TOTAL_STRINGS * self.PACKETS_PER_STRING * self.BMS_PER_PACKET * self.TEMPS_PER_BMS

    def initialize_fake_data(self):
        """Başlangıç sahte verilerini oluştur"""
        print("🔧 Sahte veriler başlatılıyor...")
        
        for string_id in range(1, self.TOTAL_STRINGS + 1):
            for packet_id in range(1, self.PACKETS_PER_STRING + 1):
                
                # Ana sistem parametreleri
                self.soc_values[(string_id, packet_id)] = random.uniform(80.0, 95.0)
                self.soh_values[(string_id, packet_id)] = random.uniform(95.0, 99.5)
                self.currents[(string_id, packet_id)] = random.uniform(-100.0, 50.0)
                
                # Hücre voltajları
                cell_count = 0
                total_voltage = 0.0
                
                for bms_id in range(1, self.BMS_PER_PACKET + 1):
                    cells_in_bms = self.CELLS_PER_BMS[bms_id - 1]
                    
                    for cell_in_bms in range(1, cells_in_bms + 1):
                        cell_count += 1
                        base_voltage = random.uniform(3.65, 3.75)
                        self.cell_voltages[(string_id, packet_id, cell_count)] = base_voltage
                        total_voltage += base_voltage
                
                self.pack_voltages[(string_id, packet_id)] = total_voltage
                
                # Sıcaklık sensörleri
                temp_count = 0
                for bms_id in range(1, self.BMS_PER_PACKET + 1):
                    for temp_sensor in range(1, self.TEMPS_PER_BMS + 1):
                        temp_count += 1
                        base_temp = random.uniform(20.0, 35.0)
                        self.temperatures[(string_id, packet_id, temp_count)] = base_temp

    def voltage_to_bytes(self, voltage):
        """Voltajı CAN formatındaki byte'lara çevir (reverse engineering)"""
        # convert_voltage fonksiyonunun tersi: voltage = (cell_val * 0.00015) + 1.5024
        cell_val = int((voltage - 1.5024) / 0.00015)
        if cell_val < 0:
            cell_val = cell_val + 65535 - 1
        
        high_byte = (cell_val >> 8) & 0xFF
        low_byte = cell_val & 0xFF
        return [high_byte, low_byte]

    def temp_to_voltage_bytes(self, temp_celsius):
        """Sıcaklığı CAN formatındaki byte'lara çevir"""
        # Temperature formülünün tersi ile voltage hesapla
        try:
            # t_celsius = t_kelvin - 273.15 -> t_kelvin = t_celsius + 273.15
            t_kelvin = temp_celsius + 273.15
            # 1 / t_kelvin = 1 / 298.15 - math.log(10000 / ntc) / 4100
            # math.log(10000 / ntc) = (1 / 298.15 - 1 / t_kelvin) * 4100
            log_ratio = (1 / 298.15 - 1 / t_kelvin) * 4100
            # 10000 / ntc = exp(log_ratio) -> ntc = 10000 / exp(log_ratio)
            import math
            ntc = 10000 / math.exp(log_ratio)
            # ntc = volt * 10000 / (3 - volt) -> volt = 3 * ntc / (ntc + 10000)
            volt = 3 * ntc / (ntc + 10000)
            return self.voltage_to_bytes(volt)
        except:
            return self.voltage_to_bytes(1.5)  # Fallback value

    def create_can_message(self, string_id, packet_id, bms_id):
        """Belirli bir BMS için 64-byte CAN mesajı oluştur"""
        data = [0x00] * 64
        
        # BMS'in packet içindeki sırası (1-6)
        bms_in_packet = bms_id
        
        # Sıcaklık verileri (7 sensör x 2 byte = 14 byte)
        temp_offset = 0
        for temp_sensor in range(1, self.TEMPS_PER_BMS + 1):
            global_temp_index = (bms_in_packet - 1) * self.TEMPS_PER_BMS + temp_sensor
            temp_key = (string_id, packet_id, global_temp_index)
            
            if temp_key in self.temperatures:
                temp_celsius = self.temperatures[temp_key]
                temp_bytes = self.temp_to_voltage_bytes(temp_celsius)
            else:
                temp_bytes = [0x00, 0x00]
            
            data[temp_offset] = temp_bytes[1]      # Low byte
            data[temp_offset + 1] = temp_bytes[0]  # High byte
            temp_offset += 2
        
        # VAREF (2 byte) - sabit değer
        data[14] = 0x80
        data[15] = 0x0C
        
        # Hücre voltajları (18 hücre x 2 byte = 36 byte)
        voltage_offset = 16
        cells_in_bms = self.CELLS_PER_BMS[bms_in_packet - 1]
        
        # BMS offset hesaplama
        if bms_in_packet <= 5:
            bms_offset = (bms_in_packet - 1) * 18
        else:  # bms_in_packet == 6
            bms_offset = 5 * 18  # İlk 5 BMS'in toplam hücresi = 90
        
        for cell_index in range(1, 19):  # Her zaman 18 slot var
            if cell_index <= cells_in_bms:
                global_cell_number = bms_offset + cell_index
                cell_key = (string_id, packet_id, global_cell_number)
                
                if cell_key in self.cell_voltages:
                    voltage = self.cell_voltages[cell_key]
                    voltage_bytes = self.voltage_to_bytes(voltage)
                else:
                    voltage_bytes = [0x00, 0x00]
            else:
                voltage_bytes = [0x00, 0x00]  # Kullanılmayan hücre slotları
            
            data[voltage_offset] = voltage_bytes[1]      # Low byte
            data[voltage_offset + 1] = voltage_bytes[0]  # High byte
            voltage_offset += 2
        
        # DGS verileri (3 byte)
        data[52] = random.randint(0, 255)
        data[53] = random.randint(0, 255) 
        data[54] = random.randint(0, 255)
        
        # Boş alan (1 byte)
        data[55] = 0x00
        
        # Pressure (4 byte float)
        pressure_value = random.uniform(1.0, 3.0)
        pressure_bytes = struct.pack('f', pressure_value)
        for i, b in enumerate(pressure_bytes):
            data[56 + i] = b
        
        # Current (4 byte float)
        current_key = (string_id, packet_id)
        if current_key in self.currents:
            current_value = self.currents[current_key]
        else:
            current_value = 0.0
        current_bytes = struct.pack('f', current_value)
        for i, b in enumerate(current_bytes):
            data[60 + i] = b
        
        return data

    def generate_can_id(self, string_id, packet_id, bms_id):
        """CAN ID oluştur (reverse engineering)"""
        # CAN ID format: [response_bit:1][string_id:4][bms_id:5][packet_bit:1]
        response_bit = 1  # Yanıt mesajı
        
        # Global BMS ID hesapla (1-24 arası)
        global_bms_id = (packet_id - 1) * 6 + bms_id
        
        # Packet bit (0 veya 1)
        packet_bit = (packet_id - 1) % 2
        
        can_id = (response_bit << 10) | (string_id << 6) | (global_bms_id << 1) | packet_bit
        return can_id

    def update_simulation_data(self):
        """Simülasyon verilerini güncelle (gerçekçi değişimler)"""
        
        for string_id in range(1, self.TOTAL_STRINGS + 1):
            for packet_id in range(1, self.PACKETS_PER_STRING + 1):
                
                # SOC azalması (şarj tükenmesi simülasyonu)
                soc_key = (string_id, packet_id)
                if soc_key in self.soc_values:
                    self.soc_values[soc_key] = max(10.0, 
                        self.soc_values[soc_key] - random.uniform(0.1, 0.3))
                
                # SOH çok yavaş azalması
                soh_key = (string_id, packet_id)
                if soh_key in self.soh_values:
                    self.soh_values[soh_key] = max(90.0,
                        self.soh_values[soh_key] - random.uniform(0.001, 0.01))
                
                # Akım değişimi
                current_key = (string_id, packet_id)
                if current_key in self.currents:
                    current_change = random.uniform(-5.0, 5.0)
                    self.currents[current_key] = max(-200.0, min(100.0,
                        self.currents[current_key] + current_change))
                
                # Hücre voltajları (küçük değişimler)
                cell_count = 0
                total_voltage = 0.0
                
                for bms_id in range(1, self.BMS_PER_PACKET + 1):
                    cells_in_bms = self.CELLS_PER_BMS[bms_id - 1]
                    
                    for cell_in_bms in range(1, cells_in_bms + 1):
                        cell_count += 1
                        cell_key = (string_id, packet_id, cell_count)
                        
                        if cell_key in self.cell_voltages:
                            voltage_change = random.uniform(-0.01, 0.01)
                            new_voltage = self.cell_voltages[cell_key] + voltage_change
                            new_voltage = max(3.0, min(4.2, new_voltage))
                            self.cell_voltages[cell_key] = new_voltage
                            total_voltage += new_voltage
                
                self.pack_voltages[(string_id, packet_id)] = total_voltage
                
                # Sıcaklık değişimleri
                temp_count = 0
                for bms_id in range(1, self.BMS_PER_PACKET + 1):
                    for temp_sensor in range(1, self.TEMPS_PER_BMS + 1):
                        temp_count += 1
                        temp_key = (string_id, packet_id, temp_count)
                        
                        if temp_key in self.temperatures:
                            temp_change = random.uniform(-1.0, 2.0)
                            new_temp = self.temperatures[temp_key] + temp_change
                            new_temp = max(0.0, min(80.0, new_temp))
                            self.temperatures[temp_key] = new_temp

    def print_sample_data(self):
        """Örnek veriyi konsola yazdır"""
        print(f"\n📊 ÖRNEK SİMÜLASYON VERİLERİ ({datetime.now().strftime('%H:%M:%S')})")
        print("-" * 60)
        
        # String-1, Packet-1 örnekleri
        sample_string = 1
        sample_packet = 1
        
        # Ana parametreler
        soc_key = (sample_string, sample_packet)
        soh_key = (sample_string, sample_packet)
        current_key = (sample_string, sample_packet)
        voltage_key = (sample_string, sample_packet)
        
        if soc_key in self.soc_values:
            print(f"🔋 SOC: {self.soc_values[soc_key]:.2f}%")
        if soh_key in self.soh_values:
            print(f"💪 SOH: {self.soh_values[soh_key]:.2f}%")
        if current_key in self.currents:
            print(f"⚡ Current: {self.currents[current_key]:.2f}A")
        if voltage_key in self.pack_voltages:
            print(f"🔌 Pack Voltage: {self.pack_voltages[voltage_key]:.2f}V")
        
        # Örnek hücre voltajları (ilk 5 hücre)
        print("\n📍 Örnek Hücre Voltajları (String-1, Packet-1):")
        for cell_num in range(1, 6):
            cell_key = (sample_string, sample_packet, cell_num)
            if cell_key in self.cell_voltages:
                voltage = self.cell_voltages[cell_key]
                print(f"   Cell-{cell_num}: {voltage:.3f}V")
        
        # Örnek sıcaklık değerleri (ilk 3 sensör)
        print("\n🌡️ Örnek Sıcaklık Değerleri (String-1, Packet-1):")
        for temp_num in range(1, 4):
            temp_key = (sample_string, sample_packet, temp_num)
            if temp_key in self.temperatures:
                temp = self.temperatures[temp_key]
                print(f"   Temp-{temp_num}: {temp:.1f}°C")

    def simulate_can_messages(self):
        """Ana simülasyon döngüsü"""
        message_count = 0
        
        while self.running:
            try:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Tüm string ve paketler için mesajlar oluştur
                for string_id in range(1, self.TOTAL_STRINGS + 1):
                    for packet_id in range(1, self.PACKETS_PER_STRING + 1):
                        for bms_id in range(1, self.BMS_PER_PACKET + 1):
                            
                            # CAN ID oluştur
                            can_id = self.generate_can_id(string_id, packet_id, bms_id)
                            
                            # 64-byte mesaj oluştur
                            message_data = self.create_can_message(string_id, packet_id, bms_id)
                            
                            # Mesajı konsola yazdır (CAN dump formatında)
                            hex_data = ' '.join([f'{b:02X}' for b in message_data])
                            print(f"  can0  {can_id:03X}   [64]  {hex_data}")
                            
                            message_count += 1
                
                # Durum bilgisi
                if message_count % 100 == 0:
                    print(f"\n🎯 {message_count} mesaj gönderildi...")
                    self.print_sample_data()
                
                # Simülasyon verilerini güncelle
                self.update_simulation_data()
                
                # Bekleme
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Simülasyon durduruluyor...")
                break
            except Exception as e:
                print(f"❌ Simülasyon hatası: {e}")
                time.sleep(1)

    def start_simulation(self):
        """Simülasyonu başlat"""
        self.running = True
        print("🚀 Sahte CAN mesajları başlatılıyor...")
        print("⏹️  Durdurmak için CTRL+C basın\n")
        
        try:
            self.simulate_can_messages()
        except KeyboardInterrupt:
            print("\n✅ Simülasyon temiz şekilde durduruldu.")
        finally:
            self.running = False

    def stop_simulation(self):
        """Simülasyonu durdur"""
        self.running = False

def main():
    """Ana fonksiyon"""
    print("🔥 SAHTE CAN FD MESAJ SİMÜLATÖRÜ")
    print("=" * 50)
    print("Bu script sahte BMS CAN FD mesajları üretir:")
    print("  • 4,992 hücre voltajı")
    print("  • 2,304 sıcaklık sensörü")
    print("  • SOC, SOH, Akım, Toplam Voltaj")
    print("  • Gerçekçi veri değişimleri")
    print("=" * 50)
    
    # Simülatörü başlat
    simulator = CANMessageSimulator()
    
    try:
        simulator.start_simulation()
    except KeyboardInterrupt:
        print("\n🛑 Program sonlandırılıyor...")
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
    finally:
        simulator.stop_simulation()
        print("👋 Simülasyon tamamlandı!")

if __name__ == "__main__":
    main()
