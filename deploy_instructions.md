# YGA İrsaliye Parser - Online Deploy Rehberi

Bu web uygulamasını online yayınlamak için çeşitli seçenekleriniz bulunmaktadır:

## 1. Heroku (Ücretsiz Başlangıç)

### Gereksinimler:
- Heroku hesabı (heroku.com)
- Git kurulu olmalı
- Heroku CLI kurulu olmalı

### Adımlar:

```bash
# 1. Heroku CLI ile giriş yapın
heroku login

# 2. Heroku uygulaması oluşturun
heroku create yga-irsaliye-parser-2025

# 3. Git repository başlatın (eğer yoksa)
git init
git add .
git commit -m "Initial commit - YGA İrsaliye Parser Web App"

# 4. Heroku'ya deploy edin
git push heroku main

# 5. Uygulamayı açın
heroku open
```

## 2. Railway (Modern ve Kolay)

### Adımlar:
1. railway.app sitesine gidin
2. GitHub ile giriş yapın
3. "Deploy from GitHub repo" seçin
4. Bu projeyi seçin
5. Otomatik deploy başlayacak

## 3. Render (Ücretsiz Plan)

### Adımlar:
1. render.com sitesine gidin
2. GitHub ile giriş yapın
3. "New Web Service" seçin
4. Bu repository'i bağlayın
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn app:app`

## 4. PythonAnywhere (Python Odaklı)

### Adımlar:
1. pythonanywhere.com hesabı açın
2. Files sekmesinden dosyaları yükleyin
3. Console'dan gerekli paketleri yükleyin:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```
4. Web sekmesinden Flask uygulaması oluşturun
5. WSGI dosyasını düzenleyin

## 5. Streamlit Cloud (En Kolay)

Streamlit versiyonu için:

```python
# streamlit_app.py
import streamlit as st
from your_parser_logic import IrsaliyeParserWeb

st.title("YGA İrsaliye Parser")

uploaded_files = st.file_uploader(
    "HTML dosyalarını yükleyin",
    accept_multiple_files=True,
    type=['html', 'zip']
)

if uploaded_files:
    parser = IrsaliyeParserWeb()
    # Parser logic here
    st.download_button("CSV İndir", data=csv_data, file_name="results.csv")
```

## 6. Google Cloud Run

### Dockerfile oluşturun:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
```

### Deploy:
```bash
gcloud run deploy yga-parser --source .
```

## Önerilen Seçim: Railway

Railway en kolay ve modern seçenektir:
1. GitHub'a kod yükleyin
2. Railway.app'e gidin
3. GitHub ile bağlanın
4. Deploy edin
5. Hazır!

## Environment Variables (Gerekirse)

Çevresel değişkenler için `.env` dosyası:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=52428800
```

## Güvenlik Notları

Production için:
- `DEBUG=False` yapın
- Güçlü SECRET_KEY kullanın
- HTTPS kullanın
- File upload limitlerini ayarlayın
- Rate limiting ekleyin

## Maliyet

- **Heroku**: İlk 550 saat ücretsiz
- **Railway**: $5/ay'dan başlayan planlar
- **Render**: Ücretsiz plan mevcut
- **PythonAnywhere**: Ücretsiz plan sınırlı
- **Streamlit Cloud**: Tamamen ücretsiz (public repo için)

## Son Adım

Deploy ettikten sonra URL'i kaydedin ve kullanmaya başlayın!