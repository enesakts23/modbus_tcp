import sys
import random
import time
import can
import os
import numpy as np
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, \
    QStackedWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPalette, QFont, QFontDatabase, QPixmap, QPainterPath, QIcon
from PyQt6.QtCore import Qt, QTimer, QTime, QRectF, QThread, pyqtSignal, QMutex, QWaitCondition, QPoint, QSize
import struct
from temperature_page import TemperatureWidget, convert_temperature
from pack_view_page import PackViewWidget
from graph_page import GraphWidget
from settings_page import SettingsWidget
from string_view_page import StringViewWidget

V = np.zeros((32, 36))
float_array = []
hex_array = []
hex_data = ""
msg = ""

def convert_voltage(X):
    cell_val = 0x0000
    cell_val = (X[0] << 8) | X[1]
    if cell_val >= 0x8000:
        cell_val = cell_val - 65535 + 1
    return float(cell_val) * 0.00015 + 1.5024

class CanBusWorker(QThread):
    message_sent_signal = pyqtSignal(str, list)

    def __init__(self, interface="can0", bitrate=250000, parent=None):
        super().__init__(parent)
        self.interface = interface
        self.bitrate = bitrate
        self.can_bus = None
        self.query_id = 0x440
        self.loop_delay = 30.0
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.is_can_available = False
        self.balance_requested = False
        self.is_balancing = False
        self.balancing_cells = []
        self.balancing_current = 0
        self.CELLS_PER_BMU = 18
        self.cycle_complete = True

    def set_balancing_mode(self, cells, current):
        """Balanslama isteğini kaydet"""
        self.mutex.lock()
        self.balancing_cells = cells
        self.balancing_current = current
        self.balance_requested = True
        self.mutex.unlock()
        print("Balanslama isteği alındı, cycle sonunda başlatılacak")

    def stop_balancing_mode(self):
        """Balanslama modunu durdur ve sıfırlama mesajlarını gönder"""
        try:
            reset_messages = {
                '0x97_packet1': [0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
                '0x97_packet2': [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 
                '0x98_packet1': [0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00], 
                '0x98_packet2': [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  
            }
            message1 = can.Message(
                arbitration_id=0x97,
                data=reset_messages['0x97_packet1'],
                is_extended_id=False
            )
            self.can_bus.send(message1)
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] BALANCING STOP MESAJI GÖNDERİLDİ: ID=0x{message1.arbitration_id:03X}, Data={bytes(reset_messages['0x97_packet1']).hex().upper()}")
            time.sleep(0.1)

            message2 = can.Message(
                arbitration_id=0x97,
                data=reset_messages['0x97_packet2'],
                is_extended_id=False
            )
            self.can_bus.send(message2)
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] BALANCING STOP MESAJI GÖNDERİLDİ: ID=0x{message2.arbitration_id:03X}, Data={bytes(reset_messages['0x97_packet2']).hex().upper()}")
            time.sleep(0.1)
            message3 = can.Message(
                arbitration_id=0x98,
                data=reset_messages['0x98_packet1'],
                is_extended_id=False
            )
            self.can_bus.send(message3)
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] BALANCING STOP MESAJI GÖNDERİLDİ: ID=0x{message3.arbitration_id:03X}, Data={bytes(reset_messages['0x98_packet1']).hex().upper()}")
            time.sleep(0.1)
            message4 = can.Message(
                arbitration_id=0x98,
                data=reset_messages['0x98_packet2'],
                is_extended_id=False
            )
            self.can_bus.send(message4)
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] BALANCING STOP MESAJI GÖNDERİLDİ: ID=0x{message4.arbitration_id:03X}, Data={bytes(reset_messages['0x98_packet2']).hex().upper()}")
            time.sleep(0.1)
            print("\nBalanslama durdurma mesajları gönderildi:")
            print(f"Paket 1 (0x97, BMU 0x01-0x02) data:", ' '.join([f'0x{b:02X}' for b in reset_messages['0x97_packet1']]))
            print(f"Paket 2 (0x97, BMU 0x03) data:", ' '.join([f'0x{b:02X}' for b in reset_messages['0x97_packet2']]))
            print(f"Paket 3 (0x98, BMU 0x01-0x02) data:", ' '.join([f'0x{b:02X}' for b in reset_messages['0x98_packet1']]))
            print(f"Paket 4 (0x98, BMU 0x03) data:", ' '.join([f'0x{b:02X}' for b in reset_messages['0x98_packet2']]))

        except Exception as e:
            print(f"Balanslama durdurma mesajları gönderilirken hata: {e}")
        finally:
            self.mutex.lock()
            self.balance_requested = False
            self.is_balancing = False
            self.balancing_cells = []
            self.balancing_current = 0
            self.mutex.unlock()
            print("Balanslama modu durduruldu")

    def create_balancing_message(self):
        try:
            packets = {
                '0x97_packet1': [0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
                '0x97_packet2': [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 
                '0x98_packet1': [0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
                '0x98_packet2': [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 
            }

            for cell_num in self.balancing_cells:
                if 1 <= cell_num <= 54: 
                    bmu_index = (cell_num - 1) // 18 
                    cell_in_bmu = ((cell_num - 1) % 18) + 1 
                    byte_index = (cell_in_bmu - 1) // 8 
                    bit_position = (cell_in_bmu - 1) % 8

                    if bmu_index == 0:
                        packets['0x97_packet1'][1 + byte_index] |= (1 << bit_position)
                    elif bmu_index == 1: 
                        packets['0x97_packet1'][5 + byte_index] |= (1 << bit_position)
                    elif bmu_index == 2: 
                        packets['0x97_packet2'][1 + byte_index] |= (1 << bit_position)

                elif 55 <= cell_num <= 104: 
                    normalized_cell = cell_num - 54
                    bmu_index = (normalized_cell - 1) // 18
                    cell_in_bmu = ((normalized_cell - 1) % 18) + 1

                    byte_index = (cell_in_bmu - 1) // 8
                    bit_position = (cell_in_bmu - 1) % 8

                    if bmu_index == 0: 
                        packets['0x98_packet1'][1 + byte_index] |= (1 << bit_position)
                    elif bmu_index == 1: 
                        packets['0x98_packet1'][5 + byte_index] |= (1 << bit_position)
                    elif bmu_index == 2: 
                        packets['0x98_packet2'][1 + byte_index] |= (1 << bit_position)

            return packets
        except Exception as e:
            print(f"Balancing mesajı oluşturulurken hata: {e}")
            return {
                '0x97_packet1': [0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
                '0x97_packet2': [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
                '0x98_packet1': [0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
                '0x98_packet2': [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            }
    def run(self):
        try:
            print("CAN arayüzü ayarlanıyor...")            
            os.system("sudo ip link set can0 down")
            print(f"✓ {self.interface} kapatıldı")            
            os.system(f"sudo ip link set can0 type can bitrate {self.bitrate}")
            print(f"✓ Bitrate {self.bitrate} olarak ayarlandı")            
            os.system("sudo ip link set can0 up")
            print(f"✓ {self.interface} açıldı")            
            self.can_bus = can.interface.Bus(channel=self.interface, bustype='socketcan', bitrate=self.bitrate)
            print(f"✓ CAN bus {self.interface} başarıyla bağlandı")
            print(f"CAN interface {self.interface} initialized at {self.bitrate}bps.")
            self.is_can_available = True
        except Exception as e:
            print(f"CAN initialization error: {e}")
            print("Running without CAN bus")
            self.is_can_available = False
        print(f"Sorgu döngüsü başlatıldı.")
        print(f"Sorgu ID: 0x{self.query_id:03X} | Her {self.loop_delay} saniyede bir sorgu gönderilecek")
        print("=" * 60)
        
        query_count = 0
        while True:
            if self.is_can_available:
                try:
                    if not self.is_balancing:
                        self.cycle_complete = False
                        query_count += 1
                        print(f"--- SORGU #{query_count} ---")
                        success = self.send_query()
                        if success:
                            print(f"✓ Sorgu başarıyla gönderildi")
                        else:
                            print(f"✗ Sorgu gönderilemedi")
                        
                        responses = self.wait_for_can_responses(timeout=30)
                        if responses:
                            print(f"📨 {len(responses)} adet 64-byte mesaj alındı, parse ediliyor...")
                            self.message_sent_signal.emit(f"Query Response", responses)
                        else:
                            print(f"Sorguya yanıt alınamadı")
                            
                        self.cycle_complete = True
                        print(f"⏳ {self.loop_delay} saniye bekleniyor...\n")
                        self.mutex.lock()
                        if self.balance_requested and self.cycle_complete:
                            self.is_balancing = True
                            print("Veri toplama cycle'ı tamamlandı, balancing başlatılıyor")
                        self.mutex.unlock()

                    if self.is_balancing:
                        try:
                            message_data = self.create_balancing_message()
                            message1 = can.Message(
                                arbitration_id=0x97,
                                data=message_data['0x97_packet1'],
                                is_extended_id=False
                            )
                            self.can_bus.send(message1)
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"[{timestamp}] BALANCING MESAJI GÖNDERİLDİ: ID=0x{message1.arbitration_id:03X}, Data={bytes(message_data['0x97_packet1']).hex().upper()}")
                            time.sleep(0.1)
                            message2 = can.Message(
                                arbitration_id=0x97,
                                data=message_data['0x97_packet2'],
                                is_extended_id=False
                            )
                            self.can_bus.send(message2)
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"[{timestamp}] BALANCING MESAJI GÖNDERİLDİ: ID=0x{message2.arbitration_id:03X}, Data={bytes(message_data['0x97_packet2']).hex().upper()}")
                            time.sleep(0.1)
                            message3 = can.Message(
                                arbitration_id=0x98,
                                data=message_data['0x98_packet1'],
                                is_extended_id=False
                            )
                            self.can_bus.send(message3)
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"[{timestamp}] BALANCING MESAJI GÖNDERİLDİ: ID=0x{message3.arbitration_id:03X}, Data={bytes(message_data['0x98_packet1']).hex().upper()}")
                            time.sleep(0.1)

                            # Paket 2: Üçüncü BMU (0x03)
                            message4 = can.Message(
                                arbitration_id=0x98,
                                data=message_data['0x98_packet2'],
                                is_extended_id=False
                            )
                            self.can_bus.send(message4)
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"[{timestamp}] BALANCING MESAJI GÖNDERİLDİ: ID=0x{message4.arbitration_id:03X}, Data={bytes(message_data['0x98_packet2']).hex().upper()}")
                            time.sleep(0.1)

                            print("\nBalanslama mesajları gönderildi:")
                            print(f"Paket 1 (0x97, BMU 0x01-0x02) data:",
                                  ' '.join([f'0x{b:02X}' for b in message_data['0x97_packet1']]))
                            print(f"Paket 2 (0x97, BMU 0x03) data:",
                                  ' '.join([f'0x{b:02X}' for b in message_data['0x97_packet2']]))
                            print(f"Paket 3 (0x98, BMU 0x01-0x02) data:",
                                  ' '.join([f'0x{b:02X}' for b in message_data['0x98_packet1']]))
                            print(f"Paket 4 (0x98, BMU 0x03) data:",
                                  ' '.join([f'0x{b:02X}' for b in message_data['0x98_packet2']]))
                        except Exception as e:
                            print(f"Balancing mesajı gönderilirken hata: {e}")
                        finally:
                            self.mutex.lock()
                            self.is_balancing = False
                            self.balance_requested = False
                            self.mutex.unlock()
                            print("Balancing işlemi tamamlandı, normal veri toplamaya dönülüyor")

                except Exception as e:
                    print(f"CAN communication error: {e}")
                    if self.is_can_available:
                        print(f"Sorgu döngüsü hatası: {e}")
                    time.sleep(1)

            time.sleep(self.loop_delay)
    def send_query(self, data=None):
        """0x440 ID'sine sorgu gönder"""
        if data is None:
            data = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]
        
        try:
            message = can.Message(
                arbitration_id=self.query_id,
                data=data,
                is_extended_id=False
            )
            self.can_bus.send(message)
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] SORGU GÖNDERİLDİ: ID=0x{message.arbitration_id:03X}, Data={bytes(data).hex().upper()}")
            return True
        except Exception as e:
            print(f"Gönderim hatası: {e}")
            return False

    def wait_for_can_responses(self, timeout=30):
        """Gelen CAN mesajlarını dinle - 24 mesaj gelince hemen döndür"""
        responses = []
        message_count = 0
        
        try:
            process = subprocess.Popen(
                ['candump', self.interface],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    line = process.stdout.readline()
                    if line:
                        message_count += 1
                        timestamp = time.strftime('%H:%M:%S.%f')[:-3]
                        print(f"[{timestamp}] {line.strip()}")
                        try:
                            parts = line.strip().split()
                            if len(parts) >= 3:
                                can_id_str = parts[1]  
                                if can_id_str.isalnum():
                                    can_id = int(can_id_str, 16)
                                    bracket_found = False
                                    data_bytes = []
                                    for part in parts[2:]:
                                        if '[' in part:
                                            bracket_found = True
                                            continue
                                        if bracket_found and len(part) == 2:
                                            try:
                                                data_bytes.append(int(part, 16))
                                            except ValueError:
                                                pass
                                    
                                    if len(data_bytes) == 64:
                                        responses.append({'can_id': hex(can_id), 'data': data_bytes})
                                        print(f"✓ 64 byte mesaj #{len(responses)} toplandı - ID=0x{can_id:X}")
                                        
                                        if len(responses) >= 24:
                                            print(f"🎯 24 MESAJ TOPLANDI! Parse işlemi başlatılıyor...")
                                            break
                                    else:
                                        print(f"⚠ Beklenmeyen veri boyutu: {len(data_bytes)} byte (64 byte bekleniyor) - ID=0x{can_id:X}")
                        except Exception as parse_error:
                            print(f"Parse hatası: {parse_error}")
                        
                except Exception as e:
                    break
                    
                if process.poll() is not None:
                    break
                    
            try:
                process.terminate()
                process.wait(timeout=1)
            except:
                process.kill()
                process.wait()
                
        except FileNotFoundError:
            print("❌ 'candump' komutu bulunamadı! can-utils paketini yükleyin:")
            print("   sudo apt-get install can-utils")
            return None
        except Exception as e:
            print(f"Mesaj dinleme hatası: {e}")
            
        print(f"🛑 Dinleme tamamlandı. Toplam {message_count} candump mesajı, {len(responses)} adet 64-byte mesaj toplandı.")
        return responses if responses else None

class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setFixedHeight(55)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#020E0D"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 3, 10, 8)
        main_layout.setSpacing(12)
        logo_label = QLabel()
        logo_pixmap = QPixmap("reaplogo.png")
        scaled_pixmap = logo_pixmap.scaled(80, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(logo_label)
        self.switch_container = QWidget()
        switch_layout = QHBoxLayout(self.switch_container)
        switch_layout.setContentsMargins(0, 0, 0, 0)
        switch_layout.setSpacing(4)
        mb_label = QLabel("MB")
        mb_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        switch_layout.addWidget(mb_label)
        self.switch_button = QPushButton()
        self.switch_button.setCheckable(True)
        self.switch_button.setFixedSize(50, 26)
        self.switch_button.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: 2px solid #404040;
                border-radius: 13px;
            }
            QPushButton:checked {
                background-color: #00B294;
                border: 2px solid #008C72;
            }
        """)
        switch_layout.addWidget(self.switch_button)
        ab_label = QLabel("AB")
        ab_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        switch_layout.addWidget(ab_label)

        main_layout.addStretch(2) 
        main_layout.addWidget(self.switch_container)
        main_layout.addStretch(1) 
        self.switch_container.hide() 
        self.info_container = QWidget()
        info_layout = QHBoxLayout(self.info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)        
        self.string_label = QLabel("String: 1")
        self.string_label.setStyleSheet("""
            QLabel {
                color: #00B294;
                font-size: 10px;
                font-weight: bold;
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 3px;
                padding: 2px 4px;
                min-width: 30px;
            }
        """)
        
        self.packet_label = QLabel("Pack: 1")
        self.packet_label.setStyleSheet("""
            QLabel {
                color: #00B294;
                font-size: 10px;
                font-weight: bold;
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 3px;
                padding: 2px 4px;
                min-width: 30px;
            }
        """)
        
        info_layout.addWidget(self.string_label)
        info_layout.addWidget(self.packet_label)
        
        main_layout.addWidget(self.info_container)
        main_layout.addStretch(1) 

        self.info_container.hide()  # Başlangıçta gizli

        self.default_style = """
            QPushButton {
                background-color: #1A1A1A;
                color: #808080;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #2C2C2C;
                color: #FFFFFF;
                border: 1px solid #404040;
            }
            QPushButton:pressed {
                background-color: #404040;
                color: #FFFFFF;
            }
        """

        self.selected_style = """
            QPushButton {
                background-color: #2C2C2C;
                color: #FFFFFF;
                border: 2px solid #00B294;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
                min-height: 28px;
            }
        """

        self.buttons = []
        button_texts = ["VOLTAGE", "TEMPERATURE", "PACK VIEW", "GRAPH", "SETTINGS", "STRING VIEW"]

        for i, button_text in enumerate(button_texts):
            button = QPushButton(button_text)
            button.setStyleSheet(self.default_style)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked, index=i: self.on_button_clicked(index))
            main_layout.addWidget(button)
            self.buttons.append(button)
        power_button = QPushButton()
        power_button.setFixedSize(42, 42)
        power_button.setCursor(Qt.CursorShape.PointingHandCursor)
        power_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.1);
                border-radius: 6px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 68, 68, 0.2);
            }
        """)
        
        power_icon = QPixmap("poweroff.png")
        power_button.setIcon(QIcon(power_icon))
        power_button.setIconSize(QSize(32, 32))
        power_button.clicked.connect(lambda: QApplication.instance().quit())
        
        main_layout.addWidget(power_button)

        self.current_selected = 0
        self.buttons[0].setStyleSheet(self.selected_style)

        self.setLayout(main_layout)

    def mousePressEvent(self, event):
        if self.parent and hasattr(self.parent.voltage_widget, 'popup'):
            self.parent.voltage_widget.closePopup()
        super().mousePressEvent(event)

    def on_button_clicked(self, index):
        if self.parent and hasattr(self.parent.voltage_widget, 'popup'):
            self.parent.voltage_widget.closePopup()
        self.buttons[self.current_selected].setStyleSheet(self.default_style)
        self.buttons[index].setStyleSheet(self.selected_style)
        self.current_selected = index
        self.switch_container.setVisible(False)  # MB/AB switch'ini tamamen gizle
        self.info_container.setVisible(index in [0, 1, 3, 4])    # Voltage (0), Temperature (1), Graph (3), Settings (4) sayfalarında bilgi göster
        
        if self.parent:
            # Sayfayı değiştir
            self.parent.stack_widget.setCurrentIndex(index)
            
            # Temperature sayfasına geçildiğinde önbellekteki değerleri yükle
            if index == 1:  # Temperature sayfası
                self.parent._apply_cached_temperature_to_ui()
            # Voltage sayfasına geçildiğinde önbellekteki değerleri yükle
            elif index == 0:  # Voltage sayfası
                self.parent._apply_cached_voltage_to_ui()

    def update_info_labels(self, string_no, packet_no):
        """String ve packet bilgilerini güncelle"""
        self.string_label.setText(f"String: {string_no}")
        self.packet_label.setText(f"Pack: {packet_no}")


class CellPopup(QWidget):
    def __init__(self, cell_number, voltage, parent=None, string_no=None, packet_no=None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(300, 200)
        layout = QVBoxLayout(self)
        
        # Global BMS hesaplama (1-24 arası)
        # Her pack'te 6 BMS var, her BMS'te BMS 1-5: 18 hücre, BMS 6: 14 hücre
        
        # Önce hangi pack'teyiz belirle (varsayılan pack-1 ise packet_no kullan)
        current_pack = packet_no if packet_no is not None else 1
        
        # Pack içindeki BMS numarasını hesapla
        if cell_number <= 18:
            pack_bms_no = 1
            bms_cell = cell_number
        elif cell_number <= 36:
            pack_bms_no = 2
            bms_cell = cell_number - 18
        elif cell_number <= 54:
            pack_bms_no = 3
            bms_cell = cell_number - 36
        elif cell_number <= 72:
            pack_bms_no = 4
            bms_cell = cell_number - 54
        elif cell_number <= 90:
            pack_bms_no = 5
            bms_cell = cell_number - 72
        elif cell_number <= 104:
            pack_bms_no = 6
            bms_cell = cell_number - 90
        else:
            pack_bms_no = 0
            bms_cell = cell_number
        
        # Global BMS numarasını hesapla (1-24 arası)
        global_bms_no = (current_pack - 1) * 6 + pack_bms_no
        bms_no = f"BMS {global_bms_no}"
        
        display_string_no = string_no if string_no is not None else "Bilinmiyor"
        display_packet_no = packet_no if packet_no is not None else "Bilinmiyor"
        info_label = QLabel()
        info_text = f"String no: {display_string_no}\nCell no: {cell_number}\nRelated BMS no: {bms_no}\nCell no in BMS: {bms_cell}\nPacket no: {display_packet_no}"
        info_label.setText(info_text)
        info_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #020E0D;
                border: 2px solid #00B294;
                border-radius: 8px;
            }
        """)

        if parent:
            parent.installEventFilter(self)

    def closeEvent(self, event):
        if self.parent():
            self.parent().removeEventFilter(self)
        super().closeEvent(event)

    def showEvent(self, event):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
        super().showEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            if not self.geometry().contains(event.globalPosition().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        self.close()


class RectangleWidget(QWidget):
    def __init__(self):
        super().__init__()
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#020E0D"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        font_id = QFontDatabase.addApplicationFont("din-1451-std/DINEngschriftStd.otf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.voltage_font = QFont(font_family, 20)
        else:
            self.voltage_font = QFont("Monospace", 20, QFont.Weight.Bold)

        self.voltage_values = [[None for _ in range(13)] for _ in range(8)]
        self.last_update_times = [[0.0 for _ in range(13)] for _ in range(8)]
        self.popup = None
        self.current_string_no = 1  # Default olarak string-1
        self.current_packet_no = 1  # Default olarak pack-1        
        self.repaint_timer = QTimer(self)
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(50)

    def set_string_packet_info(self, string_no, packet_no):
        """String ve packet bilgilerini ayarla"""
        self.current_string_no = string_no
        self.current_packet_no = packet_no

    def clear_voltages(self):
        """Tüm hücre değerlerini temizle."""
        for r in range(8):
            for c in range(13):
                self.voltage_values[r][c] = None
                self.last_update_times[r][c] = 0.0
        self.update()

    def closePopup(self):
        if self.popup and self.popup.isVisible():
            self.popup.close()
        self.popup = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            width = self.width()
            height = self.height()
            columns = 13
            rows = 8
            h_spacing = 8
            margin = 20
            usable_width = width - 2 * margin
            usable_height = height - 2 * margin
            rect_width = (usable_width - (columns - 1) * h_spacing) // columns
            rect_height = int((usable_height - (rows - 1) * 8) // (rows * 1.3))
            v_spacing = (usable_height - rows * rect_height) // (rows - 1) if rows > 1 else 0
            x = event.position().x()
            y = event.position().y()

            for row in range(rows):
                for col in range(columns):
                    cell_x = margin + col * (rect_width + h_spacing)
                    cell_y = margin + row * (rect_height + v_spacing)
                    
                    if (cell_x <= x <= cell_x + rect_width and 
                        cell_y <= y <= cell_y + rect_height):
                        cell_number = row * 13 + col + 1
                        voltage = self.voltage_values[row][col]
                        self.closePopup()
                        self.popup = CellPopup(cell_number, voltage, self, 
                                             self.current_string_no, self.current_packet_no)
                        self.popup.destroyed.connect(lambda: setattr(self, 'popup', None))
                        self.popup.show()
                        return
            self.closePopup()

    def get_package_min_max(self):
        """Her paket için min ve max değerleri ve konumlarını hesapla"""
        package1_min = float('inf')
        package1_max = float('-inf')
        package2_min = float('inf')
        package2_max = float('-inf')
        package1_min_pos = None
        package1_max_pos = None
        package2_min_pos = None
        package2_max_pos = None

        for row in range(8):
            for col in range(13):
                cell_number = row * 13 + col + 1
                voltage = self.voltage_values[row][col]

                if voltage is not None:
                    if cell_number <= 54: 
                        if voltage < package1_min:
                            package1_min = voltage
                            package1_min_pos = (row, col)
                        if voltage > package1_max:
                            package1_max = voltage
                            package1_max_pos = (row, col)
                    else: 
                        if voltage < package2_min:
                            package2_min = voltage
                            package2_min_pos = (row, col)
                        if voltage > package2_max:
                            package2_max = voltage
                            package2_max_pos = (row, col)

        if package1_min == float('inf'):
            package1_min = None
            package1_min_pos = None
        if package1_max == float('-inf'):
            package1_max = None
            package1_max_pos = None
        if package2_min == float('inf'):
            package2_min = None
            package2_min_pos = None
        if package2_max == float('-inf'):
            package2_max = None
            package2_max_pos = None

        return {
            'package1': {
                'min': package1_min,
                'max': package1_max,
                'min_pos': package1_min_pos,
                'max_pos': package1_max_pos
            },
            'package2': {
                'min': package2_min,
                'max': package2_max,
                'min_pos': package2_min_pos,
                'max_pos': package2_max_pos
            }
        }

    def update_cell_voltage(self, cell_number, voltage):
        """Hücre voltajını güncelle - yeni 64 byte format için"""
        if 1 <= cell_number <= 104: 
            row = (cell_number - 1) // 13
            col = (cell_number - 1) % 13
            self.voltage_values[row][col] = voltage
            self.last_update_times[row][col] = QTime.currentTime().msecsSinceStartOfDay() / 1000.0
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        package_values = self.get_package_min_max()
        width = self.width()
        height = self.height()
        columns = 13
        rows = 8
        h_spacing = 8
        margin = 20
        usable_width = width - 2 * margin
        usable_height = height - 2 * margin
        rect_width = (usable_width - (columns - 1) * h_spacing) // columns
        rect_height = int((usable_height - (rows - 1) * 8) // (rows * 1.3))
        total_rect_height = rows * rect_height
        remaining_space = usable_height - total_rect_height
        v_spacing = remaining_space // (rows - 1) if rows > 1 else 0
        start_x = margin
        start_y = margin
        normal_color = QColor("#2C2C2C")
        warning_color = QColor("#FFD700")
        danger_color = QColor("#FF0000")
        text_white = QColor("#FFFFFF")
        text_green = QColor("#00FF00")
        border_color = QColor(255, 255, 255, 50)
        current_time = QTime.currentTime().msecsSinceStartOfDay() / 1000.0
        corner_radius = 8

        for row in range(rows):
            for col in range(columns):
                x = int(start_x + col * (rect_width + h_spacing))
                y = int(start_y + row * (rect_height + v_spacing))
                voltage = self.voltage_values[row][col]
                cell_number = row * 13 + col + 1

                rect = QRectF(x, y, rect_width, rect_height)

                if voltage is None:
                    painter.setBrush(QBrush(normal_color))
                    painter.setPen(QPen(border_color, 1))
                    painter.drawRoundedRect(rect, corner_radius, corner_radius)
                    continue

                current_package = 'package1' if cell_number <= 54 else 'package2'
                package_data = package_values[current_package]

                if voltage > 3.80 or voltage < 2.50:
                    painter.setBrush(QBrush(danger_color))
                    painter.setPen(QPen(border_color, 1))
                    painter.drawRoundedRect(rect, corner_radius, corner_radius)
                else:
                    painter.setBrush(QBrush(normal_color))
                    painter.setPen(QPen(border_color, 1))
                    painter.drawRoundedRect(rect, corner_radius, corner_radius)

                    if package_data['max_pos'] == (row, col):
                        painter.setPen(QPen(warning_color, 2))
                        path = QPainterPath()
                        path.moveTo(x + corner_radius, y)
                        path.lineTo(x + rect_width - corner_radius, y)
                        path.arcTo(x + rect_width - 2 * corner_radius, y, 2 * corner_radius, 2 * corner_radius, 90, -90)
                        path.lineTo(x + rect_width, y + rect_height / 2 - 1)
                        path.moveTo(x, y + rect_height / 2 - 1)
                        path.lineTo(x, y + corner_radius)
                        path.arcTo(x, y, 2 * corner_radius, 2 * corner_radius, 180, -90)
                        painter.drawPath(path)

                    if package_data['min_pos'] == (row, col):
                        painter.setPen(QPen(warning_color, 2))
                        path = QPainterPath()
                        path.moveTo(x + rect_width, y + rect_height / 2 + 1)
                        path.lineTo(x + rect_width, y + rect_height - corner_radius)
                        path.arcTo(x + rect_width - 2 * corner_radius, y + rect_height - 2 * corner_radius,
                                   2 * corner_radius, 2 * corner_radius, 0, -90)
                        path.lineTo(x + corner_radius, y + rect_height)
                        path.arcTo(x, y + rect_height - 2 * corner_radius, 2 * corner_radius, 2 * corner_radius, -90,
                                   -90)
                        path.lineTo(x, y + rect_height / 2 + 1)
                        painter.drawPath(path)

                voltage_text = f"{voltage:.2f}"

                font_size = int(min(rect_width * 0.30, rect_height * 0.65))
                font = self.voltage_font
                font.setPixelSize(font_size)
                painter.setFont(font)

                text_rect = painter.fontMetrics().boundingRect(voltage_text)
                while text_rect.width() > rect_width * 0.9:
                    font_size -= 1
                    font.setPixelSize(font_size)
                    painter.setFont(font)
                    text_rect = painter.fontMetrics().boundingRect(voltage_text)

                time_since_update = current_time - self.last_update_times[row][col]
                if voltage > 3.80 or voltage < 2.50:
                    text_color = text_white
                elif (row, col) in [package_data['min_pos'], package_data['max_pos']]:
                    text_color = warning_color
                elif time_since_update < 1.0:
                    text_color = text_green
                else:
                    text_color = text_white

                painter.setPen(text_color)
                text_x = x + (rect_width - text_rect.width()) // 2
                text_y = y + (rect_height + text_rect.height()) // 2 - 2
                painter.drawText(text_x, text_y, voltage_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("REAP BATTERY VOLTAGE DASHBOARD")
        self.setFixedSize(1024, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header = HeaderWidget(self)
        layout.addWidget(self.header)

        self.stack_widget = QStackedWidget()
        self.voltage_widget = RectangleWidget()
        self.temperature_widget = TemperatureWidget()
        self.pack_view_widget = PackViewWidget()
        self.graph_widget = GraphWidget()
        self.settings_widget = SettingsWidget()
        self.string_view_widget = StringViewWidget()

        self.settings_widget.balancing_started.connect(self.handle_balancing_started)
        self.settings_widget.balancing_stopped.connect(self.handle_balancing_stopped)

        self.stack_widget.addWidget(self.voltage_widget)
        self.stack_widget.addWidget(self.temperature_widget)
        self.stack_widget.addWidget(self.pack_view_widget)
        self.stack_widget.addWidget(self.graph_widget)
        self.stack_widget.addWidget(self.settings_widget)
        self.stack_widget.addWidget(self.string_view_widget)

        layout.addWidget(self.stack_widget)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Kullanıcı seçimi: başlangıçta String-1 / Pack-1 ve otomatik değişmeyecek
        self.selected_string_no = 1
        self.selected_packet_no = 1

        # Her (string, pack) için en son verileri önbellekle
        # Voltajlar: dict[(string, pack)] -> { cell_no(1-104): float }
        # Sıcaklıklar: dict[(string, pack)] -> { temp_index(0-41): float }
        self.voltage_cache = {}
        self.temp_cache = {}

        self.can_worker = CanBusWorker()
        self.can_worker.message_sent_signal.connect(self.process_can_data)
        self.can_worker.start()

    def set_user_selection(self, string_no: int, packet_no: int):
        """String View üzerinden kullanıcı seçim yaptığında merkezi seçimi güncelle."""
        self.selected_string_no = int(string_no)
        self.selected_packet_no = int(packet_no)
        # İlgili widget'ların bağlamını güncelle
        if hasattr(self, 'voltage_widget'):
            self.voltage_widget.set_string_packet_info(self.selected_string_no, self.selected_packet_no)
        if hasattr(self, 'temperature_widget'):
            self.temperature_widget.set_string_packet_info(self.selected_string_no, self.selected_packet_no)
        if hasattr(self, 'graph_widget'):
            self.graph_widget.set_string_packet_info(self.selected_string_no, self.selected_packet_no)
        if hasattr(self, 'settings_widget'):
            self.settings_widget.set_string_packet_info(self.selected_string_no, self.selected_packet_no)
        if hasattr(self, 'header'):
            self.header.update_info_labels(self.selected_string_no, self.selected_packet_no)

        # Seçim değiştiğinde, önbellekten ekrana uygula
        self._apply_cached_voltage_to_ui()
        self._apply_cached_temperature_to_ui()

    def _apply_cached_voltage_to_ui(self):
        """Seçili (string, pack) için önbellekteki voltajları ekrana uygula."""
        key = (self.selected_string_no, self.selected_packet_no)
        # Önce ekranı temizle
        if hasattr(self, 'voltage_widget'):
            self.voltage_widget.clear_voltages()

        cache = self.voltage_cache.get(key)
        if not cache:
            return  # Henüz veri yoksa temiz ekran kalsın

        # Önbellekteki tüm hücreleri doldur
        for global_cell_number, voltage_value in cache.items():
            if 1 <= global_cell_number <= 104:
                self.voltage_widget.update_cell_voltage(global_cell_number, voltage_value)
                # Settings grid'i de senkron tut
                if hasattr(self, 'settings_widget'):
                    row = (global_cell_number - 1) // 13
                    col = (global_cell_number - 1) % 13
                    self.settings_widget.update_voltage(row, col, voltage_value)

    def _apply_cached_temperature_to_ui(self):
        """Seçili (string, pack) için önbellekteki sıcaklıkları ekrana uygula."""
        key = (self.selected_string_no, self.selected_packet_no)
        # Önce ekranı temizle
        if hasattr(self, 'temperature_widget'):
            self.temperature_widget.clear_temperatures()

        cache = self.temp_cache.get(key)
        if not cache:
            return  # Henüz veri yoksa temiz ekran kalsın

        # Önbellekteki tüm sıcaklık değerlerini doldur
        for global_temp_index, temp_voltage in cache.items():
            if 0 <= global_temp_index < 42:
                self.temperature_widget.update_temperature(global_temp_index, temp_voltage)

    def handle_balancing_started(self, selected_cells, current):
        print(f"Balanslama başlatılıyor: Hücreler={selected_cells}, Akım={current}mA")
        self.can_worker.set_balancing_mode(selected_cells, current)

    def handle_balancing_stopped(self):
        print("Balanslama durduruluyor...")
        self.can_worker.stop_balancing_mode()

    def process_can_data(self, node_id, responses):
        if not responses:
            return
        
        print(f"\n🔥 PROCESS_CAN_DATA ÇAĞRILDI! {len(responses)} mesaj işlenecek")
        print("=" * 100)
        
        for i, response in enumerate(responses):
            can_id = response['can_id']
            data = response['data']
            can_id_int = int(can_id, 16)
            paket_no_raw = can_id_int & 0x1 
            bms_id = (can_id_int >> 1) & 0x1F  
            string_id = (can_id_int >> 6) & 0xF  
            response_bit = (can_id_int >> 10) & 0x1  
            paket_no = ((bms_id - 1) // 6) + 1
            
            print(f"\n📦 Mesaj {i+1}/{len(responses)} - CAN ID: {can_id}")
            print(f"🔍 ID Parse: BMS={bms_id} | String={string_id} | Paket={paket_no} | Response={response_bit}")
            print(f"🔢 Binary: {can_id_int:011b} (Hex: 0x{can_id_int:02X}, Dec: {can_id_int})")
            
            if len(data) != 64:
                print(f"⚠ Beklenmeyen veri boyutu: {len(data)} byte (64 byte bekleniyor)")
                continue
            
            temp_data = {
                'T1': [data[1], data[0]], 'T2': [data[3], data[2]], 'T3': [data[5], data[4]],
                'T4': [data[7], data[6]], 'TPCB': [data[9], data[8]], 'T6': [data[11], data[10]],
                'T7': [data[13], data[12]]
            }
            varef_data = [data[15], data[14]]
            voltage_data = {}
            for j in range(18):
                v_name = f"V{j+1}"
                byte_start = 16 + (j * 2)
                voltage_data[v_name] = [data[byte_start + 1], data[byte_start]]
            
            dgs_data = {'DGS1': data[52], 'DGS2': data[53], 'DGS3': data[54]}
            pressure_data = [data[56], data[57], data[58], data[59]]
            current_data = [data[60], data[61], data[62], data[63]]
            
            print("🌡️  SICAKLIK:")
            # Seçili olmayan paketlerin UI'yi bozmasını engelle
            selected_str = getattr(self, 'selected_string_no', 1)
            selected_pack = getattr(self, 'selected_packet_no', 1)
            ui_update_allowed = (string_id == selected_str and paket_no == selected_pack)

            # Önbellek anahtarı
            cache_key = (string_id, paket_no)
            if cache_key not in self.temp_cache:
                self.temp_cache[cache_key] = {}
            if cache_key not in self.voltage_cache:
                self.voltage_cache[cache_key] = {}
            for temp_name, temp_bytes in temp_data.items():
                temp_voltage = convert_voltage(temp_bytes)
                temp_celsius = convert_temperature(temp_voltage)
                print(f"   {temp_name}: {temp_bytes[0]:02X}{temp_bytes[1]:02X} → {temp_voltage:.3f}V → {temp_celsius:.1f}°C")
                temp_index = list(temp_data.keys()).index(temp_name)
                bms_in_packet = ((bms_id - 1) % 6) + 1
                # Her BMS'in 7 sıcaklık sensörü var, toplam 42 sensör (6 BMS x 7 sensör)
                global_temp_index = (bms_in_packet - 1) * 7 + temp_index

                # Önbelleği güncelle (her zaman)
                if cache_key not in self.temp_cache:
                    self.temp_cache[cache_key] = {}
                self.temp_cache[cache_key][global_temp_index] = temp_voltage

                # Sadece seçili string/pack için UI'yi güncelle
                if string_id == self.selected_string_no and paket_no == self.selected_packet_no:
                    if hasattr(self, 'temperature_widget'):
                        self.temperature_widget.update_temperature(global_temp_index, temp_voltage)
                        if hasattr(self, 'header'):
                            self.header.update_info_labels(string_id, paket_no)
                    if hasattr(self, 'graph_widget'):
                        self.graph_widget.set_string_packet_info(string_id, paket_no)
                    if hasattr(self, 'settings_widget'):
                        self.settings_widget.set_string_packet_info(string_id, paket_no)
            
            print(f"🔌 VAREF: {varef_data[0]:02X}{varef_data[1]:02X} → {convert_voltage(varef_data):.3f}")            
            print("⚡ VOLTAJLAR:")
            bms_in_packet = ((bms_id - 1) % 6) + 1
            
            # BMS offset hesaplama - her pack'te 6 BMS var (BMS 1-5: 18 hücre, BMS 6: 14 hücre)
            if bms_in_packet <= 5:
                bms_offset = (bms_in_packet - 1) * 18
            else:  # bms_in_packet == 6
                bms_offset = 5 * 18  # İlk 5 BMS'in toplam hücresi = 90
            
            for v_name, v_bytes in voltage_data.items():
                voltage_value = convert_voltage(v_bytes)
                cell_index = int(v_name[1:])
                
                # BMS 6 için sadece ilk 14 hücreyi kabul et
                if bms_in_packet == 6 and cell_index > 14:
                    continue
                    
                global_cell_number = bms_offset + cell_index
                
                if global_cell_number > 104:
                    continue
                
                # Global BMS numarasını hesapla (1-24 arası)
                global_bms_id = (paket_no - 1) * 6 + bms_in_packet
                
                print(f"   {v_name}: {v_bytes[0]:02X}{v_bytes[1]:02X} → {voltage_value:.3f}V (Global Cell: {global_cell_number}) [Global BMS:{global_bms_id} String:{string_id} Paket:{paket_no}]")
                
                # Önbelleği güncelle (her zaman)
                self.voltage_cache[cache_key][global_cell_number] = voltage_value

                if 1 <= global_cell_number <= 104 and ui_update_allowed:
                    self.voltage_widget.update_cell_voltage(global_cell_number, voltage_value)
                    # Seçim sabit kalsın: seçili (varsayılan 1/1) değerleri kullan
                    self.voltage_widget.set_string_packet_info(selected_str, selected_pack)
                    if hasattr(self, 'temperature_widget'):
                        self.temperature_widget.set_string_packet_info(selected_str, selected_pack)
                    if hasattr(self, 'graph_widget'):
                        self.graph_widget.set_string_packet_info(selected_str, selected_pack)
                    if hasattr(self, 'settings_widget'):
                        self.settings_widget.set_string_packet_info(selected_str, selected_pack)
                        row = (global_cell_number - 1) // 13
                        col = (global_cell_number - 1) % 13
                        self.settings_widget.update_voltage(row, col, voltage_value)
            
            print(f"🔧 DGS: DGS1=0x{dgs_data['DGS1']:02X} DGS2=0x{dgs_data['DGS2']:02X} DGS3=0x{dgs_data['DGS3']:02X}")
            
            try:
                pressure_value = struct.unpack('f', bytes(pressure_data))[0]
                current_value = struct.unpack('f', bytes(current_data))[0]
                print(f"� PRESSURE: {pressure_value:.2f}")
                print(f"⚡ CURRENT: {current_value:.2f}A")
                
                if hasattr(self, 'pack_view_widget'):
                    self.pack_view_widget.update_current(current_value)
            except Exception as e:
                print(f"Float dönüşüm hatası: {e}")
            
            print("-" * 50)
        
        print("=" * 100)
        print("✅ TÜM MESAJLAR İŞLENDİ!")
        print("=" * 100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_palette = app.palette()
    app_palette.setColor(QPalette.ColorRole.Window, QColor("#020E0D"))
    #app.setOverrideCursor(Qt.CursorShape.BlankCursor)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())