# Modbus TCP İstemci/Sunucu Uygulaması

Bu proje, Modbus TCP protokolünü kullanan bir istemci ve sunucu uygulamasıdır. Python dilinde yazılmış olup, endüstriyel cihazlarla haberleşme için kullanılabilir.

## Proje Yapısı

Proje aşağıdaki ana dosyalardan oluşmaktadır:

- `tcp_client.py`: TCP soket haberleşmesini yöneten temel sınıf
- `modbus.py`: Modbus protokol işlemlerini gerçekleştiren ana sınıf
- `modbus_server.py`: Test amaçlı Modbus TCP sunucusu
- `example.py`: Örnek kullanımları gösteren test scripti

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

### Sunucuyu Başlatma

Test sunucusunu başlatmak için:
```bash
python3 modbus_server.py
```
Sunucu varsayılan olarak localhost üzerinde 1024 portunda çalışacaktır.

### İstemciyi Çalıştırma

Örnek istemci uygulamasını çalıştırmak için:
```bash
python3 example.py
```

## Modbus Harita Yapısı

### Holding Register Adresleri (4xxxx)

#### Sistem Kontrol Registerleri (0-99)
- 0: Sistem durumu
- 1: Sistem komut registeri
- 2: Hata kodu
- 3: Çalışma modu

#### Sıcaklık Kontrol Registerleri (100-199)
- 100: Sıcaklık ayar değeri
- 101: Sıcaklık kontrol modu
- 102: Sıcaklık P kazancı
- 103: Sıcaklık I kazancı
- 104: Sıcaklık D kazancı

#### Basınç Kontrol Registerleri (200-299)
- 200: Basınç ayar değeri
- 201: Basınç kontrol modu
- 202: Basınç P kazancı
- 203: Basınç I kazancı
- 204: Basınç D kazancı

#### Alarm Limitleri (300-399)
- 300: Yüksek sıcaklık alarmı
- 301: Düşük sıcaklık alarmı
- 302: Yüksek basınç alarmı
- 303: Düşük basınç alarmı

### Input Register Adresleri (3xxxx)

#### Sistem Durum Registerleri (0-99)
- 0: Sistem çalışma süresi
- 1: Sistem durum bilgisi
- 2: Hata durum bilgisi
- 3: Uyarı durum bilgisi

#### Sıcaklık Ölçüm Registerleri (100-199)
- 100: Anlık sıcaklık değeri
- 101: İşlenmemiş sıcaklık değeri
- 102: Minimum sıcaklık değeri
- 103: Maksimum sıcaklık değeri
- 104: Ortalama sıcaklık değeri

#### Basınç Ölçüm Registerleri (200-299)
- 200: Anlık basınç değeri
- 201: İşlenmemiş basınç değeri
- 202: Minimum basınç değeri
- 203: Maksimum basınç değeri
- 204: Ortalama basınç değeri

### Coil Adresleri (0xxxx)

#### Sistem Kontrol Coilleri (0-99)
- 0: Sistem aktif/pasif
- 1: Alarm reset
- 2: Acil stop
- 3: Bakım modu

#### Sıcaklık Kontrol Coilleri (100-199)
- 100: Sıcaklık kontrolü aktif/pasif
- 101: Sıcaklık otomatik mod
- 102: Sıcaklık manuel mod

#### Basınç Kontrol Coilleri (200-299)
- 200: Basınç kontrolü aktif/pasif
- 201: Basınç otomatik mod
- 202: Basınç manuel mod

### Discrete Input Adresleri (1xxxx)

#### Sistem Durum Girdileri (0-99)
- 0: Güç durumu
- 1: Sistem hazır
- 2: Alarm aktif
- 3: Uyarı aktif

#### Sıcaklık Durum Girdileri (100-199)
- 100: Sıcaklık sensörü durumu
- 101: Yüksek sıcaklık limiti
- 102: Düşük sıcaklık limiti

#### Basınç Durum Girdileri (200-299)
- 200: Basınç sensörü durumu
- 201: Yüksek basınç limiti
- 202: Düşük basınç limiti

## Fonksiyonlar ve Kullanımları

### ModbusClient Sınıfı

```python
from modbus import ModbusClient

# İstemci oluşturma
client = ModbusClient()

# Sunucuya bağlanma
client.connect("localhost", 1024)

# Coil okuma (adres 0'dan başlayarak 10 adet)
error, coils = client.read_coils(0, 10)

# Register okuma (adres 100'den başlayarak 5 adet)
error, registers = client.read_holding_registers(100, 5)

# Tek coil yazma (adres 0'a True değeri yazma)
error = client.write_single_coil(0, True)

# Tek register yazma (adres 100'e 12345 değeri yazma)
error = client.write_single_register(100, 12345)

# Çoklu coil yazma
coil_values = [True, False, True, True, False]
error = client.write_multiple_coils(10, coil_values)

# Çoklu register yazma
register_values = [111, 222, 333, 444, 555]
error = client.write_multiple_registers(200, register_values)

# Bağlantıyı kapatma
client.close()
```

## Hata Kodları

- `ModbusError.OK`: İşlem başarılı
- `ModbusError.GENERAL_ERROR`: Genel hata
- `ModbusError.ILLEGAL_FUNCTION`: Geçersiz fonksiyon kodu
- `ModbusError.ILLEGAL_ADDRESS`: Geçersiz adres
- `ModbusError.ILLEGAL_VALUE`: Geçersiz değer
- `ModbusError.COMMUNICATION_ERROR`: Haberleşme hatası
- `ModbusError.NO_RESPONSE`: Yanıt yok
- `ModbusError.WRONG_DATA`: Yanlış veri formatı

## Güvenlik Notları

1. Port numarası seçimi:
   - Linux sistemlerde 1024 altındaki portlar root yetkisi gerektirir
   - Test için 1024 ve üzeri portları kullanın
   - Gerçek cihazlar genelde 502 portunu kullanır (root yetkisi gerekir)

2. Bağlantı güvenliği:
   - Üretim ortamında güvenlik duvarı kurallarını kontrol edin
   - Gerekirse SSL/TLS kullanın
   - Uzak bağlantılarda IP kısıtlaması uygulayın

## Test ve Hata Ayıklama

Sistemin düzgün çalıştığını kontrol etmek için:

1. Önce sunucuyu başlatın:
```bash
python3 modbus_server.py
```

2. Yeni bir terminal açın ve istemciyi çalıştırın:
```bash
python3 example.py
```

3. Çıktıları kontrol edin:
- Bağlantı durumu
- Coil okuma/yazma sonuçları
- Register okuma/yazma sonuçları
- Hata mesajları

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin yeni-ozellik`)
5. Pull Request oluşturun

## Lisans

Bu proje açık kaynak olarak lisanslanmıştır. Detaylar için LICENSE dosyasına bakın.