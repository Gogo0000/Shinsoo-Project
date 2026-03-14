[app]

# ── Temel Bilgiler ────────────────────────────────────────────────────────────
title          = SistemIzleme
package.name   = sistemizleme
package.domain = com.example

source.dir     = .
source.include_exts = py,png,jpg,kv,atlas,json

version        = 1.0.0
requirements   = python3,kivy,requests,plyer,jnius,android

# ── Arka Plan Servisi ─────────────────────────────────────────────────────────
# service satırı: "etiket:dosya_yolu" formatındadır.
# Uygulama kapatıldığında bile servis hayatta kalır.
services = Monitor:service/monitor.py

# ── Ekran Yönü ────────────────────────────────────────────────────────────────
orientation = portrait

# ── Android İzinleri ─────────────────────────────────────────────────────────
# INTERNET           : HTTP POST istekleri için zorunlu
# WAKE_LOCK          : CPU'nun arka planda uyumaması için
# BATTERY_STATS      : Detaylı batarya verisi okumak için
# RECEIVE_BOOT_COMPLETED : Cihaz açılışında servisi otomatik başlatmak için
android.permissions = INTERNET, WAKE_LOCK, BATTERY_STATS, RECEIVE_BOOT_COMPLETED

# ── Android Yapılandırması ────────────────────────────────────────────────────
android.minapi    = 21
android.targetapi = 33
android.archs     = arm64-v8a, armeabi-v7a

# Ön plan servisi bildirimi için (Android 8+)
android.meta_data = android.app.foreground_service_type=dataSync

# ── Build Araçları ────────────────────────────────────────────────────────────
[buildozer]
log_level  = 2
warn_on_root = 1

# ── İmzalama (release için doldur) ───────────────────────────────────────────
# android.keystore          = myapp.keystore
# android.keystore_passwd   = mypassword
# android.keyalias          = myapp
# android.keyalias_passwd   = mypassword
