[app]
title = Shinsoo
package.name = shinsoo
package.domain = com.gogo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy,requests
orientation = portrait
android.permissions = INTERNET,WAKE_LOCK,FOREGROUND_SERVICE
android.minapi = 21
android.targetapi = 33
android.archs = arm64-v8a
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
