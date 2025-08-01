# YGA İrsaliye Parser - Web Uygulaması

HTML formatındaki irsaliyelerden veri çıkarma web uygulaması.

## Özellikler

- **Çoklu Dosya Desteği**: HTML dosyalarını tek tek veya ZIP arşivi olarak yükleyebilirsiniz
- **Drag & Drop**: Dosyaları sürükleyip bırakarak yükleyebilirsiniz
- **Otomatik Encoding**: Farklı karakter kodlamaları otomatik olarak tespit edilir
- **Responsive Tasarım**: Mobil ve masaüstü cihazlarda optimize çalışır
- **CSV/JSON Export**: Sonuçları CSV veya JSON formatında indirebilirsiniz

## Çıkarılan Veriler

- İrsaliye numarası ve tarihi
- Sevk adresi bilgileri
- Sevk edilen kişi adı ve telefonu
- Malzeme kodu, açıklama ve adet bilgileri
- Açıklamalar kısmındaki not bilgileri

## Kurulum ve Çalıştırma

### Yerel Kurulum

```bash
# Gerekli paketleri yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
python app.py
```

Uygulama http://localhost:5000 adresinde çalışacaktır.

### Heroku'ya Deploy

```bash
# Heroku CLI ile deploy
heroku create yga-irsaliye-parser
git add .
git commit -m "Initial commit"
git push heroku main
```

## Kullanım

1. Ana sayfada "Dosya Seç" butonuna tıklayın veya dosyaları sürükleyip bırakın
2. HTML dosyalarını veya HTML dosyaları içeren ZIP arşivini seçin
3. "İşlemeyi Başlat" butonuna tıklayın
4. Sonuçlar sayfasında verileri görüntüleyin
5. CSV veya JSON formatında sonuçları indirin

## Desteklenen Dosya Formatları

- `.html` - Tekil HTML dosyaları
- `.zip` - HTML dosyalarını içeren ZIP arşivleri

## Teknik Detaylar

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, JavaScript
- **HTML Parser**: BeautifulSoup4
- **Encoding Desteği**: UTF-8, UTF-16, Latin-1, CP1252
- **File Upload**: Çoklu dosya ve ZIP arşiv desteği

## Güvenlik

- Dosya boyutu limiti: 50MB
- Güvenli dosya adları (secure_filename)
- Sadece HTML ve ZIP dosyaları kabul edilir
- Upload klasörleri otomatik temizlenir