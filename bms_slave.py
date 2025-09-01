import socket
import struct
import time
import random
import json
import os
import traceback
from dataclasses import dataclass
from typing import List
from bms_register_map import (
    BMSRegisters, BMSInputs, BMSCoils,
    BMS_INITIAL_VALUES, BMS_INPUT_VALUES, BMS_COIL_VALUES,
    BMSDataConverter, BMSAddressCalculator
)

@dataclass
class ModbusMapping:
    tab_bits: List[bool]
    tab_input_bits: List[bool] 
    tab_registers: List[int]
    tab_input_registers: List[int]

class MegaBMSSlave:
    def __init__(self, host: str = "0.0.0.0", port: int = 1024):
        self.host = host
        self.port = port
        self.socket = None
        self.mapping = None
        self.last_update = time.time()
        self.data_file = "bms_data.json"  # CAN simulator'dan gelen veri dosyası
        self.use_fake_data = False  # Başlangıçta gerçek veriler kullanılır
        
    def mapping_new(self, nb_bits: int, nb_input_bits: int, 
                   nb_registers: int, nb_input_registers: int) -> ModbusMapping:

        return ModbusMapping(
            tab_bits=[False] * nb_bits,
            tab_input_bits=[False] * nb_input_bits,
            tab_registers=[0] * nb_registers,
            tab_input_registers=[0] * nb_input_registers
        )
        
    def initialize_mega_bms_data(self):
        # 32-bit float register'ları başlat
        for register, value in BMS_INITIAL_VALUES.items():
            if register < len(self.mapping.tab_registers):
                self.mapping.tab_registers[register] = value
                
        print("🔋 4,992 hücre voltajı başlatılıyor (32-bit float format)...")
        base_voltage = 3.73  # 3.73V
        for string_no in range(1, 13): 
            for packet_no in range(1, 5): 
                for cell_no in range(1, 105): 
                    try:
                        address = BMSAddressCalculator.get_cell_voltage_address(string_no, packet_no, cell_no)
                        if address + 1 < len(self.mapping.tab_registers):
                            variation = random.uniform(-0.01, 0.01)  # ±10mV
                            voltage = base_voltage + variation
                            high_reg, low_reg = BMSDataConverter.float_to_registers(voltage)
                            self.mapping.tab_registers[address] = high_reg
                            self.mapping.tab_registers[address + 1] = low_reg
                    except Exception as e:
                        print(f"Hücre {string_no}-{packet_no}-{cell_no} başlatma hatası: {e}")
        
        print("🌡️ 2,304 sıcaklık sensörü başlatılıyor (32-bit float format)...")
        base_temp = 25.0  # 25°C
        for string_no in range(1, 13):  
            for packet_no in range(1, 5):  
                for bms_no in range(1, 7):  
                    for sensor_no in range(1, 9): 
                        try:
                            address = BMSAddressCalculator.get_temperature_address(string_no, packet_no, bms_no, sensor_no)
                            if address + 1 < len(self.mapping.tab_registers):
                                variation = random.uniform(-3.0, 3.0)  # ±3°C
                                temperature = base_temp + variation
                                high_reg, low_reg = BMSDataConverter.float_to_registers(temperature)
                                self.mapping.tab_registers[address] = high_reg
                                self.mapping.tab_registers[address + 1] = low_reg
                        except Exception as e:
                            print(f"Sensör {string_no}-{packet_no}-{bms_no}-{sensor_no} başlatma hatası: {e}")
                
        for input_addr, value in BMS_INPUT_VALUES.items():
            offset = input_addr - 20000
            if 0 <= offset < len(self.mapping.tab_input_bits):
                self.mapping.tab_input_bits[offset] = value
                
        for coil_addr, value in BMS_COIL_VALUES.items():
            if coil_addr < len(self.mapping.tab_registers):
                self.mapping.tab_registers[coil_addr] = value
        
        # Test amaçlı bazı coil'leri aktif et
        print("🔧 Test coil'leri başlatılıyor...")
        for i in range(10):
            if i < len(self.mapping.tab_bits):
                self.mapping.tab_bits[i] = (i % 2 == 0)  # Çift numaralı coil'ler aktif
                
        print("✅ Mega BMS başlatma tamamlandı (32-bit float format)!")
    
    def load_can_data(self):
        """CAN simulator'dan gelen verileri oku"""
        try:
            if not os.path.exists(self.data_file):
                print(f"⚠️ {self.data_file} bulunamadı, sahte veri kullanılıyor")
                self.use_fake_data = True
                return None
                
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Dosya yaşını kontrol et (5 saniyeden eski ise sahte veri kullan)
            file_time = os.path.getmtime(self.data_file)
            current_time = time.time()
            
            if current_time - file_time > 5.0:
                print(f"⚠️ {self.data_file} eski (5s+), sahte veri kullanılıyor")
                self.use_fake_data = True
                return None
                
            self.use_fake_data = False
            return data
            
        except Exception as e:
            print(f"❌ CAN veri okuma hatası: {e}, sahte veri kullanılıyor")
            self.use_fake_data = True
            return None
    
    def update_from_can_data(self):
        """CAN verilerinden BMS register'larını güncelle"""
        can_data = self.load_can_data()
        
        if can_data is None or self.use_fake_data:
            return  # Sahte veri kullanılacak
            
        try:
            main_data = can_data.get('main_data', {})
            
            # Ana BMS verilerini güncelle (32-bit float format)
            if 'soc' in main_data:
                soc = float(main_data['soc'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(soc)
                self.mapping.tab_registers[BMSRegisters.SOC_HIGH] = high_reg
                self.mapping.tab_registers[BMSRegisters.SOC_LOW] = low_reg
                
            if 'soh' in main_data:
                soh = float(main_data['soh'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(soh)
                self.mapping.tab_registers[BMSRegisters.SOH_HIGH] = high_reg
                self.mapping.tab_registers[BMSRegisters.SOH_LOW] = low_reg
                
            if 'pack_voltage' in main_data:
                voltage = float(main_data['pack_voltage'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(voltage)
                self.mapping.tab_registers[BMSRegisters.TOTAL_VOLTAGE_HIGH] = high_reg
                self.mapping.tab_registers[BMSRegisters.TOTAL_VOLTAGE_LOW] = low_reg
                
            if 'current' in main_data:
                current = float(main_data['current'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(current)
                self.mapping.tab_registers[BMSRegisters.CURRENT_HIGH] = high_reg
                self.mapping.tab_registers[BMSRegisters.CURRENT_LOW] = low_reg
                
            if 'max_temperature' in main_data:
                temp = float(main_data['max_temperature'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(temp)
                self.mapping.tab_registers[BMSRegisters.MAX_TEMPERATURE_HIGH] = high_reg
                self.mapping.tab_registers[BMSRegisters.MAX_TEMPERATURE_LOW] = low_reg
            
            # Coil register'ları güncelle
            if 'avg_temperature' in main_data:
                avg_temp = float(main_data['avg_temperature'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(avg_temp)
                self.mapping.tab_registers[BMSCoils.AVG_TEMP_HIGH] = high_reg
                self.mapping.tab_registers[BMSCoils.AVG_TEMP_LOW] = low_reg
                
            if 'avg_cell_voltage' in main_data:
                avg_cellv = float(main_data['avg_cell_voltage'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(avg_cellv)
                self.mapping.tab_registers[BMSCoils.AVG_CELLV_HIGH] = high_reg
                self.mapping.tab_registers[BMSCoils.AVG_CELLV_LOW] = low_reg
                
            if 'pack_voltage' in main_data:
                pack_volt = float(main_data['pack_voltage'])
                high_reg, low_reg = BMSDataConverter.float_to_registers(pack_volt)
                self.mapping.tab_registers[BMSCoils.PACK_VOLT_HIGH] = high_reg
                self.mapping.tab_registers[BMSCoils.PACK_VOLT_LOW] = low_reg
            
            # Hücre voltajlarını güncelle (varsa)
            cell_voltages = can_data.get('cell_voltages', {})
            for cell_name, voltage in cell_voltages.items():
                try:
                    # "string_1_packet_1_cell_1" formatından parse et
                    parts = cell_name.split('_')
                    if len(parts) >= 6:
                        string_no = int(parts[1])
                        packet_no = int(parts[3])
                        cell_no = int(parts[5])
                        
                        address = BMSAddressCalculator.get_cell_voltage_address(string_no, packet_no, cell_no)
                        if address + 1 < len(self.mapping.tab_registers):
                            high_reg, low_reg = BMSDataConverter.float_to_registers(float(voltage))
                            self.mapping.tab_registers[address] = high_reg
                            self.mapping.tab_registers[address + 1] = low_reg
                except:
                    continue
            
            # Sıcaklık sensörlerini güncelle (varsa)
            temperatures = can_data.get('temperatures', {})
            for temp_name, temperature in temperatures.items():
                try:
                    # "string_1_packet_1_temp_1" formatından parse et
                    parts = temp_name.split('_')
                    if len(parts) >= 6:
                        string_no = int(parts[1])
                        packet_no = int(parts[3])
                        temp_no = int(parts[5])
                        
                        # Temp_no'yu BMS ve sensor'e çevir (basit hesaplama)
                        bms_no = ((temp_no - 1) // 7) + 1
                        sensor_no = ((temp_no - 1) % 7) + 1
                        
                        if bms_no <= 6 and sensor_no <= 8:
                            address = BMSAddressCalculator.get_temperature_address(string_no, packet_no, bms_no, sensor_no)
                            if address + 1 < len(self.mapping.tab_registers):
                                high_reg, low_reg = BMSDataConverter.float_to_registers(float(temperature))
                                self.mapping.tab_registers[address] = high_reg
                                self.mapping.tab_registers[address + 1] = low_reg
                except:
                    continue
                    
            print(f"📡 CAN verilerinden güncellendi: SOC={main_data.get('soc', 0):.1f}%, "
                  f"Current={main_data.get('current', 0):.1f}A, "
                  f"Voltage={main_data.get('pack_voltage', 0):.1f}V")
                  
        except Exception as e:
            print(f"❌ CAN veri işleme hatası: {e}")
            self.use_fake_data = True
    
    def simulate_mega_bms_data(self):
        """4992 hücreli ve 2304 sensörlü BMS verilerini simüle eder"""
        try:
            # Önce JSON dosyasından veri okumaya çalış
            json_data_loaded = False
            try:
                if os.path.exists("bms_data.json"):
                    with open("bms_data.json", "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                    
                    # JSON verisindeki main_data'yı kullan
                    main_data = json_data.get("main_data", {})
                    if main_data:
                        # SOC güncelle
                        if "soc_percent" in main_data:
                            soc_value = float(main_data["soc_percent"])
                            high_reg, low_reg = BMSDataConverter.float_to_registers(soc_value)
                            self.mapping.tab_registers[BMSRegisters.SOC_HIGH] = high_reg
                            self.mapping.tab_registers[BMSRegisters.SOC_LOW] = low_reg
                        
                        # Total Voltage güncelle
                        if "total_voltage" in main_data:
                            voltage_value = float(main_data["total_voltage"])
                            high_reg, low_reg = BMSDataConverter.float_to_registers(voltage_value)
                            self.mapping.tab_registers[BMSCoils.PACK_VOLT_HIGH] = high_reg
                            self.mapping.tab_registers[BMSCoils.PACK_VOLT_LOW] = low_reg
                        
                        # Current güncelle
                        if "current" in main_data:
                            current_value = float(main_data["current"])
                            high_reg, low_reg = BMSDataConverter.float_to_registers(current_value)
                            self.mapping.tab_registers[BMSRegisters.CURRENT_HIGH] = high_reg
                            self.mapping.tab_registers[BMSRegisters.CURRENT_LOW] = low_reg
                    
                    # JSON'dan hücre voltajlarını güncelle
                    cell_update_count = 0
                    if "cell_voltages" in json_data:
                        for cell_key, voltage in json_data["cell_voltages"].items():
                            try:
                                cell_num = int(cell_key.replace("cell_", ""))
                                if cell_num <= 100:  # İlk 100 hücre
                                    # String 1, Packet 1 olarak varsayıyoruz
                                    string_no = ((cell_num - 1) // 104) + 1
                                    packet_no = (((cell_num - 1) % 104) // 26) + 1
                                    cell_no = ((cell_num - 1) % 26) + 1
                                    
                                    address = BMSAddressCalculator.get_cell_voltage_address(string_no, packet_no, cell_no)
                                    if address + 1 < len(self.mapping.tab_registers):
                                        high_reg, low_reg = BMSDataConverter.float_to_registers(float(voltage))
                                        self.mapping.tab_registers[address] = high_reg
                                        self.mapping.tab_registers[address + 1] = low_reg
                                        cell_update_count += 1
                            except:
                                continue
                    
                    # JSON'dan sıcaklıkları güncelle
                    temp_update_count = 0
                    if "temperatures" in json_data:
                        for temp_key, temp in json_data["temperatures"].items():
                            try:
                                temp_num = int(temp_key.replace("temp_", ""))
                                if temp_num <= 50:  # İlk 50 sensör
                                    # String 1, Packet 1, BMS 1 olarak varsayıyoruz
                                    string_no = ((temp_num - 1) // 8) + 1
                                    packet_no = 1
                                    bms_no = 1
                                    sensor_no = ((temp_num - 1) % 8) + 1
                                    
                                    address = BMSAddressCalculator.get_temperature_address(string_no, packet_no, bms_no, sensor_no)
                                    if address + 1 < len(self.mapping.tab_registers):
                                        high_reg, low_reg = BMSDataConverter.float_to_registers(float(temp))
                                        self.mapping.tab_registers[address] = high_reg
                                        self.mapping.tab_registers[address + 1] = low_reg
                                        temp_update_count += 1
                            except:
                                continue
                    
                    json_data_loaded = True
                    soc = main_data.get("soc_percent", 0)
                    voltage = main_data.get("total_voltage", 0)
                    current = main_data.get("current", 0)
                    print(f"📊 JSON verisi kullanıldı - SOC: {soc:.1f}%, Voltaj: {voltage:.1f}V, Akım: {current:.1f}A, {cell_update_count} hücre, {temp_update_count} sensör güncellendi")
                        
            except Exception as json_error:
                print(f"⚠️ JSON okuma hatası: {json_error}")
            
            # JSON verisi yüklenemezse hata ver
            if not json_data_loaded:
                print(f"❌ CAN simulator'ı çalışmıyor! bms_data.json dosyası bulunamadı veya okunamadı.")
                print(f"🔧 fake_can_simulator.py'yi başlatın!")
                return
            
        except Exception as e:
            print(f"❌ BMS veri simülasyonu hatası: {e}")
            traceback.print_exc()
        
        # Akım güncelle (32-bit float format)
        current_high = self.mapping.tab_registers[BMSRegisters.CURRENT_HIGH]
        current_low = self.mapping.tab_registers[BMSRegisters.CURRENT_LOW]
        current_current = BMSDataConverter.registers_to_float(current_high, current_low)
        variation = random.uniform(-5.0, 5.0)  # ±5A
        new_current = current_current + variation
        new_high, new_low = BMSDataConverter.float_to_registers(new_current)
        self.mapping.tab_registers[BMSRegisters.CURRENT_HIGH] = new_high
        self.mapping.tab_registers[BMSRegisters.CURRENT_LOW] = new_low
        
        # Max sıcaklık güncelle (örnek amaçlı)
        max_temp = 25.0 + random.uniform(-2.0, 5.0)
        max_temp_high, max_temp_low = BMSDataConverter.float_to_registers(max_temp)
        self.mapping.tab_registers[BMSRegisters.MAX_TEMPERATURE_HIGH] = max_temp_high
        self.mapping.tab_registers[BMSRegisters.MAX_TEMPERATURE_LOW] = max_temp_low
        
        # Coil değerlerini güncelle (32-bit float format)
        # Average Temperature
        avg_temp = 25.0 + random.uniform(-2.0, 5.0)
        avg_temp_high, avg_temp_low = BMSDataConverter.float_to_registers(avg_temp)
        self.mapping.tab_registers[BMSCoils.AVG_TEMP_HIGH] = avg_temp_high
        self.mapping.tab_registers[BMSCoils.AVG_TEMP_LOW] = avg_temp_low
        
        # Average Cell Voltage
        avg_cell_voltage = 3.65 + random.uniform(-0.1, 0.1)
        avg_cellv_high, avg_cellv_low = BMSDataConverter.float_to_registers(avg_cell_voltage)
        self.mapping.tab_registers[BMSCoils.AVG_CELLV_HIGH] = avg_cellv_high
        self.mapping.tab_registers[BMSCoils.AVG_CELLV_LOW] = avg_cellv_low
        
        # Pack Voltage
        pack_voltage = 403.2 + random.uniform(-5.0, 5.0)
        pack_volt_high, pack_volt_low = BMSDataConverter.float_to_registers(pack_voltage)
        self.mapping.tab_registers[BMSCoils.PACK_VOLT_HIGH] = pack_volt_high
        self.mapping.tab_registers[BMSCoils.PACK_VOLT_LOW] = pack_volt_low
        
    def tcp_listen(self, max_connections: int = 1) -> bool:

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(max_connections)
            return True
        
        except Exception as e:
            print(f"Socket oluşturma hatası: {e}")
            return False
            
    def tcp_accept(self) -> socket.socket:

        try:
            client_socket, _ = self.socket.accept()
            return client_socket
        except Exception as e:
            print(f"Bağlantı kabul hatası: {e}")
            return None
            
    def receive(self, client_socket: socket.socket) -> bytes:

        try:
            data = client_socket.recv(260)
            if not data:
                return None
            return data
        except Exception as e:
            print(f"Veri alma hatası: {e}")
            return None
            
    def reply(self, client_socket: socket.socket, query: bytes) -> bool:

        try:
            if len(query) < 8:
                return False
                
            transaction_id, protocol_id, length, unit_id = struct.unpack('>HHHB', query[:7])
            function_code = query[7]
            
            print(f"[MODBUS] Function Code: {function_code:02X}, Unit ID: {unit_id}, Address: {length}")
            
            # Her istek öncesi veriyi güncelle
            self.simulate_mega_bms_data()
            
            if function_code == 0x03: 
                address, count = struct.unpack('>HH', query[8:12])
                print(f"[DEBUG] Function 03: Reading {count} registers from address {address}")
                response_data = bytearray()
                
                for i in range(count):
                    reg_addr = address + i
                    if reg_addr < len(self.mapping.tab_registers):
                        value = self.mapping.tab_registers[reg_addr]
                    else:
                        value = 0
                    response_data.extend(struct.pack('>H', value))
                    
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, len(response_data) + 3, unit_id, function_code) + bytes([len(response_data)]) + response_data
                    
            elif function_code == 0x04:  # Read Input Registers
                address, count = struct.unpack('>HH', query[8:12])
                print(f"[DEBUG] Function 04: Reading {count} input registers from address {address}")
                response_data = bytearray()
                
                for i in range(count):
                    reg_addr = address + i
                    if reg_addr < len(self.mapping.tab_input_registers):
                        value = self.mapping.tab_input_registers[reg_addr]
                    else:
                        value = 0
                    response_data.extend(struct.pack('>H', value))
                    
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, len(response_data) + 3, unit_id, function_code) + bytes([len(response_data)]) + response_data
                    
            elif function_code == 0x02:  
                address, count = struct.unpack('>HH', query[8:12])
                print(f"[DEBUG] Function 02: Reading {count} discrete inputs from address {address}")
                byte_count = (count + 7) // 8
                response_data = bytearray(byte_count)
                
                for i in range(count):
                    input_addr = address + i - 20000  
                    if 0 <= input_addr < len(self.mapping.tab_input_bits):
                        if self.mapping.tab_input_bits[input_addr]:
                            response_data[i // 8] |= (1 << (i % 8))
                            
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, byte_count + 3, unit_id, function_code) + bytes([byte_count]) + response_data
                    
            elif function_code == 0x01:  # Read Coils - Standard bit tabanlı
                address, count = struct.unpack('>HH', query[8:12])
                print(f"[DEBUG] Function 01: Reading {count} coils from address {address}")
                byte_count = (count + 7) // 8
                response_data = bytearray(byte_count)
                
                # Coil'leri bit olarak işle
                for i in range(count):
                    coil_addr = address + i
                    if 0 <= coil_addr < len(self.mapping.tab_bits):
                        if self.mapping.tab_bits[coil_addr]:
                            response_data[i // 8] |= (1 << (i % 8))
                            
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, byte_count + 3, unit_id, function_code) + bytes([byte_count]) + response_data
                    
            elif function_code == 0x06: 
                address, value = struct.unpack('>HH', query[8:12])
                if address < len(self.mapping.tab_registers):
                    self.mapping.tab_registers[address] = value
                    print(f"[MEGA BMS] Register {address} güncellendi: {value}")
                response = query  
                
            elif function_code == 0x05: # Write Single Coil - Standard bit tabanlı
                address, value = struct.unpack('>HH', query[8:12])
                
                # Standard coil yazma işlemi
                coil_addr = address
                if 0 <= coil_addr < len(self.mapping.tab_bits):
                    self.mapping.tab_bits[coil_addr] = (value == 0xFF00)
                    print(f"[MEGA BMS] Coil {address} güncellendi: {'ON' if value == 0xFF00 else 'OFF'}")
                        
                response = query  # Echo back request  
                
            else:
                print(f"[ERROR] Desteklenmeyen function code: {function_code:02X}")
                # Exception response: 0x01 = Illegal Function
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, 3, unit_id, function_code | 0x80) + bytes([0x01])
                
            client_socket.send(response)
            return True
            
        except Exception as e:
            print(f"Yanıt gönderme hatası: {e}")
            return False
            
    def close(self):
        if self.socket:
            self.socket.close()
            
def run_mega_bms_slave():

    slave = MegaBMSSlave()
    slave.mapping = slave.mapping_new(50000, 50000, 50000, 50000)
    slave.initialize_mega_bms_data()
    
    if not slave.tcp_listen():
        print("Socket açılamadı")
        return
        
    print(f"� MEGA BMS TCP Slave başlatılıyor (port {slave.port})...")
    print("\n" + "="*80)
    print("🏭 MEGA BATARYA YÖNETİM SİSTEMİ (BMS)")
    print("="*80)
    print("📊 Sistem Kapasitesi:")
    print("  🔋 Toplam Hücre: 4,992 (12 String × 4 Paket × 104 Hücre)")
    print("  🌡️ Toplam Sensör: 2,304 (12 String × 4 Paket × 6 BMS × 8 Sensör)")
    print("  📡 Toplam Register: ~15,000")
    print("\n📍 Register Adresleri:")
    print("  🔋 Hücre Voltajları: 1010 - 6001")
    print("  🌡️ Sıcaklık Sensörleri: 7000 - 9303")
    print("  ⚡ Ana Veriler: 1000-1004, 10000-10004")
    print("  🎛️ Kontrol: 10050-10053")
    print("  ⚠️ Alarmlar: 20000-20015")
    print("  🔧 Komutlar: 30000-30005")
    
    print("\n🔢 Örnek Adres Hesaplamaları:")
    try:
        addr1 = BMSAddressCalculator.get_cell_voltage_address(1, 1, 1)
        addr2 = BMSAddressCalculator.get_cell_voltage_address(12, 4, 104)
        temp_addr1 = BMSAddressCalculator.get_temp_sensor_address(1, 1, 1, 1)
        temp_addr2 = BMSAddressCalculator.get_temp_sensor_address(12, 4, 6, 8)
        
        print(f"  📍 String-1, Paket-1, Hücre-1: {addr1}")
        print(f"  📍 String-12, Paket-4, Hücre-104: {addr2}")
        print(f"  🌡️ String-1, Paket-1, BMS-1, Sensör-1: {temp_addr1}")
        print(f"  🌡️ String-12, Paket-4, BMS-6, Sensör-8: {temp_addr2}")
    except Exception as e:
        print(f"  ❌ Adres hesaplama hatası: {e}")
    
    print("\n" + "="*80)
    
    try:
        while True:
            client_socket = slave.tcp_accept()
            if not client_socket:
                continue
                
            print(f"\n🔗 Master bağlandı - MEGA BMS verileri aktarılıyor...")
            
            while True:
                query = slave.receive(client_socket)
                if not query:
                    print("📴 Master bağlantısını kapattı, yeni Master bekleniyor...")
                    break
                    
                slave.reply(client_socket, query)
                
    except KeyboardInterrupt:
        print("\n🛑 MEGA BMS Slave kapatılıyor...")
    finally:
        slave.close()

if __name__ == "__main__":
    run_mega_bms_slave()
