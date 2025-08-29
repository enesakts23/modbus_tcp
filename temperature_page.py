from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPalette, QColor, QFont, QPainter, QPen, QBrush, QFontDatabase, QLinearGradient, QRadialGradient
from PyQt6.QtCore import Qt, QTimer, QTime, QRectF, QPointF
import math

def convert_temperature(volt):
    try:
        ntc = volt * 10000 / (3 - volt)
        t_kelvin = 1 / (1 / 298.15 - math.log(10000 / ntc) / 4100)
        t_celsius = t_kelvin - 273.15
        return t_celsius
    except Exception as e:
        print(f"Temperature conversion error: {e}")
        return 0.0

class TemperatureWidget(QWidget):
    def __init__(self):
        super().__init__()
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        font_id = QFontDatabase.addApplicationFont("din-1451-std/DINEngschriftStd.otf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.temp_font = QFont(font_family, 20)
        else:
            self.temp_font = QFont("Monospace", 20, QFont.Weight.Bold)

        self.temp_values = [0.0] * 42
        self.last_update_times = [0.0] * 42
        self.current_string_no = 1 
        self.current_packet_no = 1
        self.temp_names = {}
        for i in range(42): 
            bms_index = i // 7
            sensor_index = i % 7
            if sensor_index == 0:
                self.temp_names[i] = f"BMS{bms_index + 1} T1"
            elif sensor_index == 1:
                self.temp_names[i] = f"BMS{bms_index + 1} T2"
            elif sensor_index == 2:
                self.temp_names[i] = f"BMS{bms_index + 1} T3"
            elif sensor_index == 3:
                self.temp_names[i] = f"BMS{bms_index + 1} T4"
            elif sensor_index == 4:
                self.temp_names[i] = f"BMS{bms_index + 1} TPCB"
            elif sensor_index == 5:
                self.temp_names[i] = f"BMS{bms_index + 1} T6"
            elif sensor_index == 6:
                self.temp_names[i] = f"BMS{bms_index + 1} T7"

        self.repaint_timer = QTimer(self)
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(50)

    def clear_temperatures(self):
        """Tüm sıcaklık değerlerini temizle."""
        self.temp_values = [0.0] * 42
        self.last_update_times = [0.0] * 42
        self.update()

    def set_string_packet_info(self, string_no, packet_no):
        """String ve packet bilgilerini ayarla - volta sayfasındaki gibi"""
        self.current_string_no = string_no
        self.current_packet_no = packet_no
        self.clear_temperatures()  # Yeni string/pack seçildiğinde değerleri temizle

    def update_temperature(self, sensor_index, voltage):
        """Sıcaklık değerini güncelle"""
        if 0 <= sensor_index < 42:
            temperature = convert_temperature(voltage)
            self.temp_values[sensor_index] = temperature
            self.last_update_times[sensor_index] = QTime.currentTime().msecsSinceStartOfDay() / 1000.0
            self.update()

    def draw_metallic_box(self, painter, rect, base_color, is_warning=False, is_danger=False):
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if is_danger:
            base = QColor("#8B0000")
            highlight = QColor("#FF0000")
        elif is_warning:
            base = QColor("#8B6914")
            highlight = QColor("#FFD700")
        else:
            base = base_color
            highlight = base_color.lighter(120)

        gradient.setColorAt(0, highlight)
        gradient.setColorAt(0.4, base)
        gradient.setColorAt(0.6, base)
        gradient.setColorAt(1, highlight)
        painter.setPen(QPen(base_color.darker(150), 2))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 8, 8)
        screw_radius = 4
        screw_color = QColor("#808080")
        screw_positions = [
            QPointF(rect.left() + 8, rect.top() + 8),
            QPointF(rect.right() - 8, rect.top() + 8),
            QPointF(rect.left() + 8, rect.bottom() - 8),
            QPointF(rect.right() - 8, rect.bottom() - 8)
        ]

        for pos in screw_positions:
            screw_gradient = QRadialGradient(pos, screw_radius)
            screw_gradient.setColorAt(0, screw_color.lighter(150))
            screw_gradient.setColorAt(1, screw_color.darker(150))
            painter.setBrush(QBrush(screw_gradient))
            painter.setPen(QPen(screw_color.darker(200), 1))
            painter.drawEllipse(pos, screw_radius, screw_radius)
            start_point = QPointF(pos.x() - screw_radius / 2, pos.y())
            end_point = QPointF(pos.x() + screw_radius / 2, pos.y())
            painter.drawLine(start_point, end_point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width() 
        height = self.height() 
        columns = 7
        rows = 6
        h_spacing = 2 
        v_spacing = 2  
        margin = 2  
        label_height = 25  
        usable_width = width - 2 * margin
        usable_height = height - 2 * margin
        box_width = (usable_width - (columns - 1) * h_spacing) // columns
        box_height = (usable_height - (rows - 1) * v_spacing - rows * label_height) // rows
        total_width = columns * box_width + (columns - 1) * h_spacing
        total_height = rows * (box_height + label_height) + (rows - 1) * v_spacing
        start_x = (width - total_width) // 2
        start_y = (height - total_height) // 2
        base_color = QColor("#1a1a1a")
        text_color = QColor("#FFFFFF")
        current_time = QTime.currentTime().msecsSinceStartOfDay() / 1000.0

        for i in range(42):
            row = i // columns
            col = i % columns
            x = start_x + col * (box_width + h_spacing)
            y = start_y + row * (box_height + label_height + v_spacing)
            temperature = self.temp_values[i]
            label_rect = QRectF(x, y, box_width, label_height)
            label_gradient = QLinearGradient(label_rect.topLeft(), label_rect.bottomRight())
            label_gradient.setColorAt(0, QColor("#1a1a1a"))
            label_gradient.setColorAt(1, QColor("#000000"))
            painter.setBrush(QBrush(label_gradient))
            painter.setPen(QPen(QColor("#333333"), 1))
            painter.drawRoundedRect(label_rect, 3, 3)
            sensor_text = f"{self.temp_names[i]}"
            label_font = QFont(self.temp_font)
            label_font.setPixelSize(14)  
            painter.setFont(label_font)
            painter.setPen(text_color)
            text_rect = painter.fontMetrics().boundingRect(sensor_text)
            painter.drawText(
                x + (box_width - text_rect.width()) // 2,
                y + (label_height + text_rect.height()) // 2 - 2,
                sensor_text
            )

            temp_rect = QRectF(x, y + label_height + 1, box_width, box_height - 1)
            is_warning = False
            is_danger = False
            if temperature is not None:
                is_warning = temperature > 45
                is_danger = temperature > 60
            self.draw_metallic_box(painter, temp_rect, base_color, is_warning, is_danger)

            # Varsayılan olarak sıcaklık değerini göster
            temp_text = f"{temperature:.1f}°C" if temperature is not None else "---"
            font_size = int(min(box_width, box_height) * 0.3)  
            font = self.temp_font
            font.setPixelSize(font_size)
            painter.setFont(font)

            text_rect = painter.fontMetrics().boundingRect(temp_text)
            while text_rect.width() > box_width * 0.9:
                font_size -= 1
                font.setPixelSize(font_size)
                painter.setFont(font)
                text_rect = painter.fontMetrics().boundingRect(temp_text)

            time_since_update = current_time - self.last_update_times[i]
            
            # 10 saniyeden uzun süredir veri gelmediyse "NO DATA" göster
            if time_since_update > 10.0:
                temp_text = "NO DATA"
                text_color = QColor("#FF6B6B")  # Kırmızımsı renk
                base_color = QColor("#2C2C2C")  # Daha koyu arka plan
            elif temperature is None:
                text_color = QColor("#808080")  # Gri renk - değer yok
            elif temperature > 60:
                text_color = QColor("#FFB6C1")
            elif temperature > 45:
                text_color = QColor("#FFE4B5")
            elif time_since_update < 1.0:
                text_color = QColor("#98FB98")
            else:
                text_color = QColor("#FFFFFF")

            painter.setPen(text_color)
            painter.drawText(
                x + (box_width - text_rect.width()) // 2,
                y + label_height + ((box_height + text_rect.height()) // 2),
                temp_text
            )