# 📱 Android Sistem İzleme — Kurulum Rehberi

## Proje Yapısı

```
android_monitor/
├── main.py              # Kivy UI + servis başlatıcı
├── service/
│   └── monitor.py       # Arka plan servisi (veri toplama + HTTP POST)
├── buildozer.spec       # Android derleme konfigürasyonu
└── server/
    └── app.py           # Flask API + web paneli
```

---

## 🖥️ 1. Sunucuyu Başlat (PC / VPS)

```bash
pip install flask
python server/app.py
```

Panel: **http://localhost:5000/**  
API:   **http://0.0.0.0:5000/api/report**

---

## 📱 2. Android APK Derle

### Gereksinimler (Linux/Mac)
```bash
pip install buildozer
sudo apt install git zip unzip openjdk-17-jdk autoconf libtool
```

### Derleme
```bash
cd android_monitor
buildozer android debug          # ilk derleme ~30 dk sürer
buildozer android debug deploy   # bağlı cihaza yükle
```

### APK konumu
```
bin/sistemizleme-1.0.0-debug.apk
```

---

## ⚙️ Mimari Açıklaması

### Servis Yaşam Döngüsü

```
[Kullanıcı "Başlat" tuşuna basar]
        │
        ▼
main.py → PythonService.start('service/monitor.py')
        │
        ▼
service/monitor.py — ayrı process olarak çalışır
  ├─ collect_payload()   → cihaz / batarya / RAM / CPU verisini toplar
  ├─ send_report()       → Flask API'ye POST gönderir (retry mekanizmalı)
  └─ time.sleep(30)      → INTERVAL saniye bekler, döngü tekrar başlar
        │
        ▼
[Flask server/app.py]
  ├─ POST /api/report    → veriyi alır, depolar
  └─ GET  /              → web panelinde gösterir
```

### Çevre Değişkeni Haberleşmesi

| Değişken          | Açıklama                  | Örnek                              |
|-------------------|---------------------------|------------------------------------|
| MONITOR_API_URL   | Flask endpoint adresi     | https://shinsoo.pythonanywhere.com/send-data |
| MONITOR_INTERVAL  | Gönderim aralığı (saniye) | 30                                 |
| MONITOR_STOP      | Servisi durdurma sinyali  | 1                                  |

---

## 🔐 buildozer.spec İzin Açıklamaları

| İzin                  | Neden Gerekli                          |
|-----------------------|----------------------------------------|
| INTERNET              | HTTP POST istekleri                    |
| WAKE_LOCK             | Ekran kapalıyken CPU'nun uyanık kalması |
| BATTERY_STATS         | Detaylı batarya verisi okuma           |
| RECEIVE_BOOT_COMPLETED | Cihaz açılışında otomatik servis başlatma |

---

## 🌐 API Endpoint'leri

| Method | URL            | Açıklama                    |
|--------|----------------|-----------------------------|
| POST   | /api/report    | Android'den veri kabul et   |
| GET    | /api/latest    | En son raporu getir         |
| GET    | /api/reports   | Son N raporu getir (?limit=) |
| GET    | /              | Web izleme paneli           |

---

## 💡 İpuçları

- **Aynı Wi-Fi ağı**: Hem PC hem telefon aynı ağdaysa PC'nin yerel IP'si kullanılır.
- **VPS kullanımı**: `MONITOR_API_URL` olarak public IP verin ve güvenlik duvarında 5000 portunu açın.
- **Desktop test**: `python main.py` ile masaüstünde simülasyon çalışır (psutil + plyer gerekir).
