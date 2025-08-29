1000-1001 - SOC 
1002-1003 - SOH 
1004-1005 - TOTAL_VOLTAGE 
1006-1007 - MAX_TEMPERATURE
1008-1009 - CURRENT 

1010-6001 - Cell Voltages 

7000-9303 - Temperature Sensors 

30003-30004 - AVG_TEMP (32-bit float)
30005-30006 - AVG_CELLV (32-bit float)
30007-30008 - PACK_VOLT (32-bit float) 


****************************************************************************

### READ Functions
- 0x01 - READ_COILS (Boolean coil registerleri)
- 0x02 - READ_DISCRETE_INPUTS (Boolean input registerleri)
- 0x03 - READ_HOLDING_REGISTERS (16-bit read/write registerleri)
- 0x04 - READ_INPUT_REGISTERS (16-bit read-only registerleri)

### WRITE Functions
- 0x05 - WRITE_SINGLE_COIL (Tek coil yazma)
- 0x06 - WRITE_SINGLE_REGISTER (Tek register yazma)
- 0x0F - WRITE_MULTIPLE_COILS (Çoklu coil yazma)
- 0x10 - WRITE_MULTIPLE_REGISTERS (Çoklu register yazma)

## Exception Kodları
- 0x01 - ILLEGAL_FUNCTION
- 0x02 - ILLEGAL_DATA_ADDRESS
- 0x03 - ILLEGAL_DATA_VALUE
- 0x04 - SLAVE_DEVICE_FAILURE

# BMS System Script Hiyerarşisi

bms_system/
├── 📋 bms_register_map.py      # Register adresleri ve hesaplama fonksiyonları
│   ├── BMSRegisters (enum)     # Ana register sabitleri
│   ├── BMSCoils (enum)         # Coil register sabitleri  
│   ├── BMSAddressCalculator    # Adres hesaplama sınıfı
│   ├── BMSDataConverter        # Veri dönüştürme fonksiyonları
│   └── BMS_INITIAL_VALUES      # Başlangıç değerleri
│
├── 🏭 bms_slave.py             # MEGA BMS Slave (Server)
│   ├── MegaBMSSlave            # Ana slave sınıfı
│   ├── initialize_mega_bms()   # 4,992 hücre + 2,304 sensör başlatma
│   ├── simulate_mega_bms()     # Gerçek zamanlı veri simülasyonu
│   ├── tcp_listen()            # TCP bağlantı dinleme
│   ├── reply()                 # Modbus yanıt işleme
│   └── Function Codes:
│       ├── 0x01 - Read Coils
│       ├── 0x03 - Read Holding Registers  
│       ├── 0x05 - Write Single Coil
│       └── 0x06 - Write Single Register
│
├── 🎛️ bms_master.py            # MEGA BMS Master (Client)
│   ├── MegaBMSMaster           # Ana master sınıfı
│   ├── read_main_parameters()  # Ana BMS parametreleri
│   ├── read_sample_cells()     # Örnek hücre voltajları
│   ├── read_sample_temps()     # Örnek sıcaklık sensörleri
│   ├── read_string_summary()   # String detay analizi
│   ├── read_coil_data()        # Coil register okuma
│   ├── continuous_monitoring() # Sürekli izleme modu
│   └── Interactive Menu:
│       ├── 1️⃣ Ana Parametreler
│       ├── 2️⃣ Kapsamlı Sistem Okuma
│       ├── 3️⃣ Hücre Voltajları
│       ├── 4️⃣ Sıcaklık Sensörleri
│       ├── 5️⃣ String Analizi
│       ├── 6️⃣ Sistem Durumu
│       ├── 7️⃣ Coil Verileri
│       └── 8️⃣ Sürekli İzleme
│
├── 📡 modbus.py                # Modbus TCP Protocol Stack
│   ├── ModbusMaster            # Modbus master implementasyonu
│   ├── ModbusFunctions (enum)  # Function code sabitleri
│   ├── ModbusError (enum)      # Hata kodları
│   └── Protocol Methods:
│       ├── read_coils()
│       ├── read_holding_registers()
│       ├── write_single_coil()
│       ├── write_single_register()
│       └── write_multiple_registers()
│
├── 🌐 tcp_client.py            # TCP Socket Client
│   ├── TCPClient               # TCP bağlantı sınıfı
│   ├── init()                  # Bağlantı başlatma
│   ├── send_data()             # Veri gönderme
│   ├── receive_data()          # Veri alma
│   └── close()                 # Bağlantı kapatma
│
└── 📊 bms_client.py            # Alternatif BMS Client
    ├── BMSModbusClient         # BMS özel client
    └── Specialized Methods:
        ├── read_battery_data()
        ├── read_cell_voltages()
        └── read_temperatures()


