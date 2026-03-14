[app]
title = Shinsoo
package.name = shinsoo
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Sadeleştirilmiş kütüphane listesi
requirements = python3,kivy==2.3.0,requests,plyer

# Servis tanımı doğru
services = Monitor:service/monitor.py

orientation = portrait

# Arka plan servisi için gereken ek izin eklendi
android.permissions = INTERNET, WAKE_LOCK, BATTERY_STATS, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE

android.minapi = 21
android.targetapi = 33
android.archs = arm64-v8a, armeabi-v7a

# NDK Versiyonunu buraya ekle (Hatayı çözen kısım)
android.ndk = 25b
android.ndk_path = 

# Ön plan servis tipi
android.meta_data = android.app.foreground_service_type=dataSync

[buildozer]
log_level = 2
warn_on_root = 1
