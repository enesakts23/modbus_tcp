"""
C kodundan port edilmiş Modbus TCP Slave (Server)
"""
import socket
import struct
from dataclasses import dataclass
from typing import List

@dataclass
class ModbusMapping:
    """C'deki modbus_mapping_t yapısının Python karşılığı"""
    tab_bits: List[bool]          # Coils (0x01)
    tab_input_bits: List[bool]    # Discrete Inputs (0x02)
    tab_registers: List[int]      # Holding Registers (0x03)
    tab_input_registers: List[int]  # Input Registers (0x04)

class ModbusTCPSlave:
    def __init__(self, host: str = "0.0.0.0", port: int = 1024):
        """Modbus TCP Slave oluşturucu"""
        self.host = host
        self.port = port
        self.socket = None
        self.mapping = None
        
    def mapping_new(self, nb_bits: int, nb_input_bits: int, 
                   nb_registers: int, nb_input_registers: int) -> ModbusMapping:
        """C'deki modbus_mapping_new karşılığı"""
        return ModbusMapping(
            tab_bits=[False] * nb_bits,
            tab_input_bits=[False] * nb_input_bits,
            tab_registers=[0] * nb_registers,
            tab_input_registers=[0] * nb_input_registers
        )
        
    def tcp_listen(self, max_connections: int = 1) -> bool:
        """C'deki modbus_tcp_listen karşılığı"""
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
        """C'deki modbus_tcp_accept karşılığı"""
        try:
            client_socket, _ = self.socket.accept()
            return client_socket
        except Exception as e:
            print(f"Bağlantı kabul hatası: {e}")
            return None
            
    def receive(self, client_socket: socket.socket) -> bytes:
        """C'deki modbus_receive karşılığı"""
        try:
            # MODBUS ADU = 253 bytes + MBAP (7 bytes)
            data = client_socket.recv(260)
            if not data:
                return None
            return data
        except Exception as e:
            print(f"Veri alma hatası: {e}")
            return None
            
    def reply(self, client_socket: socket.socket, query: bytes) -> bool:
        """C'deki modbus_reply karşılığı"""
        try:
            if len(query) < 8:  # MBAP (7) + Function Code (1)
                return False
                
            # MBAP alanlarını ayır
            transaction_id, protocol_id, length, unit_id = struct.unpack('>HHHB', query[:7])
            function_code = query[7]
            
            # Fonksiyon koduna göre yanıt oluştur
            if function_code == 0x01:  # Read Coils
                address, count = struct.unpack('>HH', query[8:12])
                byte_count = (count + 7) // 8
                response_data = bytearray(byte_count)
                
                for i in range(count):
                    if self.mapping.tab_bits[address + i]:
                        response_data[i // 8] |= (1 << (i % 8))
                        
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, byte_count + 3, unit_id, function_code) + bytes([byte_count]) + response_data
                    
            elif function_code == 0x03:  # Read Holding Registers
                address, count = struct.unpack('>HH', query[8:12])
                response_data = bytearray()
                
                for i in range(count):
                    value = self.mapping.tab_registers[address + i]
                    response_data.extend(struct.pack('>H', value))
                    
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, len(response_data) + 3, unit_id, function_code) + bytes([len(response_data)]) + response_data
                    
            elif function_code == 0x05:  # Write Single Coil
                address, value = struct.unpack('>HH', query[8:12])
                if value not in [0x0000, 0xFF00]:
                    response = struct.pack('>HHHBB', transaction_id, protocol_id, 3, unit_id, function_code | 0x80) + bytes([0x03])
                else:
                    self.mapping.tab_bits[address] = (value == 0xFF00)
                    response = query  # Aynı veriyi echo
                    
            elif function_code == 0x06:  # Write Single Register
                address, value = struct.unpack('>HH', query[8:12])
                self.mapping.tab_registers[address] = value
                response = query  # Aynı veriyi echo
                
            elif function_code == 0x0F:  # Write Multiple Coils
                try:
                    address, bit_count = struct.unpack('>HH', query[8:12])
                    byte_count = query[12]
                    coil_values = query[13:13+byte_count]
                    
                    for i in range(bit_count):
                        byte_idx = i // 8
                        bit_idx = i % 8
                        if byte_idx < byte_count:
                            self.mapping.tab_bits[address + i] = bool(coil_values[byte_idx] & (1 << bit_idx))
                            
                    # Yanıt: Transaction ID (2) + Protocol ID (2) + Length (2) + Unit ID (1) + 
                    #        Function Code (1) + Address (2) + Quantity (2)
                    response = struct.pack('>HHHBBHH', 
                        transaction_id, protocol_id, 6, unit_id, function_code, address, bit_count)
                except Exception as e:
                    print(f"Çoklu coil yazma hatası: {e}")
                    response = struct.pack('>HHHBB', 
                        transaction_id, protocol_id, 3, unit_id, function_code | 0x80) + bytes([0x04])
                    
            elif function_code == 0x10:  # Write Multiple Registers
                try:
                    address, reg_count = struct.unpack('>HH', query[8:12])
                    byte_count = query[12]
                    
                    if byte_count != reg_count * 2:
                        raise ValueError("Yanlış byte sayısı")
                        
                    for i in range(reg_count):
                        value = struct.unpack('>H', query[13+i*2:15+i*2])[0]
                        self.mapping.tab_registers[address + i] = value
                        
                    # Yanıt: Transaction ID (2) + Protocol ID (2) + Length (2) + Unit ID (1) + 
                    #        Function Code (1) + Address (2) + Quantity (2)
                    response = struct.pack('>HHHBBHH', 
                        transaction_id, protocol_id, 6, unit_id, function_code, address, reg_count)
                except Exception as e:
                    print(f"Çoklu register yazma hatası: {e}")
                    response = struct.pack('>HHHBB', 
                        transaction_id, protocol_id, 3, unit_id, function_code | 0x80) + bytes([0x04])
                    
            else:
                # Desteklenmeyen fonksiyon kodu
                response = struct.pack('>HHHBB', 
                    transaction_id, protocol_id, 3, unit_id, function_code | 0x80) + bytes([0x01])
                
            client_socket.send(response)
            return True
            
        except Exception as e:
            print(f"Yanıt gönderme hatası: {e}")
            return False
            
    def close(self):
        """C'deki modbus_close ve modbus_free karşılığı"""
        if self.socket:
            self.socket.close()
            
def run_slave():
    """Modbus TCP Slave çalıştır"""
    # Slave oluştur
    slave = ModbusTCPSlave()
    
    # Register ve coil'leri ayarla
    slave.mapping = slave.mapping_new(10, 10, 10, 10)
    
    # C kodundaki gibi başlangıç değerlerini ayarla
    # Coils
    slave.mapping.tab_bits[2] = True
    slave.mapping.tab_bits[3] = True
    slave.mapping.tab_bits[8] = True
    slave.mapping.tab_bits[9] = True
    
    # Discrete Inputs
    slave.mapping.tab_input_bits[0] = True   # HIGH
    slave.mapping.tab_input_bits[1] = False  # LOW
    slave.mapping.tab_input_bits[2] = True   # HIGH
    slave.mapping.tab_input_bits[6] = True
    slave.mapping.tab_input_bits[7] = True
    slave.mapping.tab_input_bits[9] = True
    
    # Holding Registers
    slave.mapping.tab_registers[0] = 0x1234
    slave.mapping.tab_registers[1] = 0x5678
    
    # Input Registers
    slave.mapping.tab_input_registers[2] = 0x9ABC
    slave.mapping.tab_input_registers[3] = 0xDEF1
    
    # Slave'i başlat
    if not slave.tcp_listen():
        print("Socket açılamadı")
        return
        
    print(f"Modbus TCP Slave başlatılıyor (port {slave.port})...")
    print("\n=== SLAVE (SERVER) MODU ===")
    print("Bu cihaz veri sağlayıcı olarak çalışıyor")
    print("Master'dan gelen komutları işleyecek\n")
    
    print("Register Haritası:")
    
    print("\nCoils (0x01):")
    for i, value in enumerate(slave.mapping.tab_bits):
        if value:
            print(f"  Adres {i}: ON")
            
    print("\nDiscrete Inputs (0x02):")
    for i, value in enumerate(slave.mapping.tab_input_bits):
        if i in [0, 1, 2, 6, 7, 9]:
            print(f"  Adres {i}: {'HIGH' if value else 'LOW'}")
            
    print("\nHolding Registers (0x03):")
    for i, value in enumerate(slave.mapping.tab_registers):
        if i in [0, 1]:
            print(f"  Adres {i}: 0x{value:04X}")
            
    print("\nInput Registers (0x04):")
    for i, value in enumerate(slave.mapping.tab_input_registers):
        if i in [2, 3]:
            print(f"  Adres {i}: 0x{value:04X}")
    
    try:
        while True:
            # Master bağlantısını kabul et
            client_socket = slave.tcp_accept()
            if not client_socket:
                continue
                
            print("\nMaster bağlandı - komutları işlemeye hazır")
            
            while True:
                # Master'dan veri al
                query = slave.receive(client_socket)
                if not query:
                    print("Master bağlantısını kapattı, yeni Master bekleniyor...")
                    break
                    
                # Yanıt gönder
                slave.reply(client_socket, query)
                
    except KeyboardInterrupt:
        print("\nSlave kapatılıyor...")
    finally:
        slave.close()

if __name__ == "__main__":
    run_slave()
