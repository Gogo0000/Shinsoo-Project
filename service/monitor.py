# service/monitor.py — Android Arka Plan Servisi
# Bu dosya PythonService tarafından ayrı bir process'te çalıştırılır.
# main.py ile DOĞRUDAN iletişim kurmaz; çevre değişkenleri üzerinden
# parametre alır.

import os
import time
import json
import datetime
import threading

# ── Temel yapılandırma ───────────────────────────────────────────────────────
API_URL  = os.environ.get('MONITOR_API_URL',  'https://shinsoo.pythonanywhere.com/send-data')
INTERVAL = int(os.environ.get('MONITOR_INTERVAL', '30'))

# ── Android Java sınıfları ───────────────────────────────────────────────────
try:
    from jnius import autoclass
    from android import mActivity

    Context        = autoclass('android.content.Context')
    BatteryManager = autoclass('android.os.BatteryManager')
    Build          = autoclass('android.os.Build')
    ActivityManager = autoclass('android.app.ActivityManager')
    _ANDROID = True
except ImportError:
    _ANDROID = False


# ── Veri Toplama Fonksiyonları ───────────────────────────────────────────────

def get_device_info():
    """Cihaz marka/model/SDK bilgisi döner."""
    if _ANDROID:
        return {
            'brand':   Build.BRAND,
            'model':   Build.MODEL,
            'device':  Build.DEVICE,
            'sdk':     Build.VERSION.SDK_INT,
            'release': Build.VERSION.RELEASE,
        }
    else:
        import platform
        return {
            'brand':   'Desktop',
            'model':   platform.node(),
            'device':  platform.machine(),
            'sdk':     None,
            'release': platform.release(),
        }


def get_battery_info():
    """Batarya seviyesi ve şarj durumu döner."""
    if _ANDROID:
        try:
            context = mActivity.getApplicationContext()
            bm = context.getSystemService(Context.BATTERY_SERVICE)
            return {
                'level':    bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY),
                'charging': bm.isCharging(),
                'voltage':  bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_VOLTAGE),
            }
        except Exception as e:
            return {'error': str(e)}
    else:
        try:
            from plyer import battery
            s = battery.status
            return {
                'level':    s.get('percentage'),
                'charging': s.get('isCharging'),
                'voltage':  None,
            }
        except Exception:
            return {'level': None, 'charging': None, 'voltage': None}


def get_memory_info():
    """RAM kullanım bilgisi döner."""
    if _ANDROID:
        try:
            context = mActivity.getApplicationContext()
            am = context.getSystemService(Context.ACTIVITY_SERVICE)
            mi = autoclass('android.app.ActivityManager$MemoryInfo')()
            am.getMemoryInfo(mi)
            total_mb    = mi.totalMem  // (1024 * 1024)
            avail_mb    = mi.availMem  // (1024 * 1024)
            used_mb     = total_mb - avail_mb
            used_pct    = round(used_mb / total_mb * 100, 1) if total_mb else None
            return {
                'total_mb': total_mb,
                'used_mb':  used_mb,
                'avail_mb': avail_mb,
                'used_pct': used_pct,
            }
        except Exception as e:
            return {'error': str(e)}
    else:
        try:
            import psutil
            vm = psutil.virtual_memory()
            return {
                'total_mb': vm.total   // (1024 * 1024),
                'used_mb':  vm.used    // (1024 * 1024),
                'avail_mb': vm.available // (1024 * 1024),
                'used_pct': vm.percent,
            }
        except Exception:
            return {}


def get_cpu_info():
    """CPU kullanım yüzdesi döner (Android'de yaklaşık)."""
    if not _ANDROID:
        try:
            import psutil
            return {'usage_pct': psutil.cpu_percent(interval=0.5)}
        except Exception:
            return {}
    # Android'de /proc/stat okuyarak yaklaşık CPU hesabı
    try:
        def read_cpu():
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            vals = [int(x) for x in line.split()[1:]]
            idle, total = vals[3], sum(vals)
            return idle, total

        idle1, total1 = read_cpu()
        time.sleep(0.3)
        idle2, total2 = read_cpu()
        delta_total = total2 - total1
        delta_idle  = idle2  - idle1
        usage = round(100.0 * (1 - delta_idle / delta_total), 1) if delta_total else None
        return {'usage_pct': usage}
    except Exception as e:
        return {'error': str(e)}


def collect_payload():
    """Tüm verileri bir dict içinde toplar."""
    return {
        'timestamp':  datetime.datetime.utcnow().isoformat() + 'Z',
        'device':     get_device_info(),
        'battery':    get_battery_info(),
        'memory':     get_memory_info(),
        'cpu':        get_cpu_info(),
    }


# ── HTTP Gönderimi ───────────────────────────────────────────────────────────

def send_report(payload, api_url, retries=3, backoff=5):
    """
    Toplanan veriyi Flask API'sine POST eder.
    Bağlantı hatasında `retries` kadar tekrar dener.
    """
    import urllib.request
    import urllib.error

    data  = json.dumps(payload).encode('utf-8')
    req   = urllib.request.Request(
        api_url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'X-Device-ID':  payload.get('device', {}).get('model', 'unknown'),
        },
        method='POST'
    )

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body   = resp.read().decode('utf-8')
                status = resp.getcode()
                _log(f'[OK] HTTP {status} ← {body[:80]}')
                return True
        except urllib.error.HTTPError as e:
            _log(f'[ERR] HTTP {e.code}: {e.reason}  (deneme {attempt}/{retries})')
        except urllib.error.URLError as e:
            _log(f'[ERR] URL hatası: {e.reason}  (deneme {attempt}/{retries})')
        except Exception as e:
            _log(f'[ERR] Beklenmeyen hata: {e}  (deneme {attempt}/{retries})')

        if attempt < retries:
            time.sleep(backoff)

    return False


# ── Loglama (Android logcat veya stdout) ────────────────────────────────────

def _log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    line = f'[monitor] {ts} {msg}'
    print(line)   # logcat'e düşer


# ── Ana Döngü ────────────────────────────────────────────────────────────────

def run_loop():
    _log(f'Servis başlatıldı. API={API_URL}  Interval={INTERVAL}s')

    while True:
        # Durdurma sinyali kontrol et
        if os.environ.get('MONITOR_STOP') == '1':
            _log('Durdurma sinyali alındı, servis sonlanıyor.')
            break

        try:
            payload = collect_payload()
            _log(f'Veri toplandı → batarya={payload["battery"].get("level")}%  '
                 f'cpu={payload["cpu"].get("usage_pct")}%')
            send_report(payload, API_URL)
        except Exception as e:
            _log(f'[FATAL] collect/send hatası: {e}')

        # INTERVAL kadar bekle, ama her saniye durdurma sinyalini kontrol et
        for _ in range(INTERVAL):
            if os.environ.get('MONITOR_STOP') == '1':
                break
            time.sleep(1)


# ── Giriş noktası ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    run_loop()
