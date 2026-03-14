# main.py — Kivy UI + Android Servis Başlatıcı
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform

# Android'e özgü importlar
if platform == 'android':
    from android import mActivity
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

    # Java sınıfları
    PythonService = autoclass('org.kivy.android.PythonService')
    Context       = autoclass('android.content.Context')
    BatteryManager = autoclass('android.os.BatteryManager')
    Build          = autoclass('android.os.Build')


class MonitorLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)

        # ── Başlık ──────────────────────────────────────────────────────────
        self.add_widget(Label(
            text='🖥️ Sistem İzleme',
            font_size='24sp',
            bold=True,
            size_hint_y=None,
            height=50
        ))

        # ── API URL ─────────────────────────────────────────────────────────
        self.add_widget(Label(text='Flask API URL:', size_hint_y=None, height=30))
        self.api_input = TextInput(
            text='https://shinsoo.pythonanywhere.com/send-data',
            multiline=False,
            size_hint_y=None,
            height=44
        )
        self.add_widget(self.api_input)

        # ── Interval ────────────────────────────────────────────────────────
        self.add_widget(Label(text='Gönderim aralığı (saniye):', size_hint_y=None, height=30))
        self.interval_input = TextInput(
            text='30',
            multiline=False,
            size_hint_y=None,
            height=44
        )
        self.add_widget(self.interval_input)

        # ── Durum etiketi ───────────────────────────────────────────────────
        self.status_label = Label(
            text='Durum: Beklemede',
            font_size='16sp',
            size_hint_y=None,
            height=60
        )
        self.add_widget(self.status_label)

        # ── Batarya / Cihaz bilgisi ─────────────────────────────────────────
        self.info_label = Label(
            text='Cihaz bilgisi yükleniyor…',
            size_hint_y=None,
            height=80
        )
        self.add_widget(self.info_label)

        # ── Butonlar ────────────────────────────────────────────────────────
        btn_layout = BoxLayout(size_hint_y=None, height=55, spacing=10)

        self.start_btn = Button(
            text='▶  Servisi Başlat',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        self.start_btn.bind(on_press=self.start_service)
        btn_layout.add_widget(self.start_btn)

        self.stop_btn = Button(
            text='⏹  Servisi Durdur',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        self.stop_btn.bind(on_press=self.stop_service)
        btn_layout.add_widget(self.stop_btn)

        self.add_widget(btn_layout)

        # ── Log alanı ───────────────────────────────────────────────────────
        self.add_widget(Label(text='Log:', size_hint_y=None, height=28))
        scroll = ScrollView()
        self.log_label = Label(
            text='',
            size_hint_y=None,
            text_size=(None, None),
            valign='top'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)

        # İlk bilgi güncellemesi
        Clock.schedule_once(self.update_device_info, 1)
        Clock.schedule_interval(self.update_device_info, 15)

    # ── Cihaz / Batarya Bilgisi ──────────────────────────────────────────────
    def update_device_info(self, dt=None):
        if platform == 'android':
            try:
                context = mActivity.getApplicationContext()
                bm = context.getSystemService(Context.BATTERY_SERVICE)
                battery_pct = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                charging    = bm.isCharging()
                brand  = Build.BRAND
                model  = Build.MODEL
                sdk    = Build.VERSION.SDK_INT
                self.info_label.text = (
                    f'📱 {brand} {model}  |  Android SDK {sdk}\n'
                    f'🔋 Batarya: %{battery_pct}  {"⚡ Şarj oluyor" if charging else ""}'
                )
            except Exception as e:
                self.info_label.text = f'Bilgi alınamadı: {e}'
        else:
            # Desktop test
            try:
                from plyer import battery, deviceid
                b = battery.status
                pct = b.get('percentage', '?')
                self.info_label.text = f'🔋 Batarya: %{pct}  (Desktop modu)'
            except Exception:
                import platform as _p
                self.info_label.text = f'🖥️ Desktop: {_p.node()}  |  {_p.system()} {_p.release()}'

    # ── Servis Başlat ────────────────────────────────────────────────────────
    def start_service(self, *args):
        api_url  = self.api_input.text.strip()
        interval = self.interval_input.text.strip() or '30'

        # Çevre değişkenleri ile servise parametre ilet
        os.environ['MONITOR_API_URL']  = api_url
        os.environ['MONITOR_INTERVAL'] = interval

        if platform == 'android':
            request_permissions([Permission.INTERNET])
            PythonService.start(
                mActivity,
                'Sistem İzleme Aktif',
                'Veriler sunucuya gönderiliyor…',
                'service/monitor.py'
            )
            self.status_label.text = f'✅ Servis aktif → {api_url}'
            self._log(f'Servis başlatıldı. Interval={interval}s')
        else:
            # Desktop test: ayrı thread'de çalıştır
            self._start_desktop_thread(api_url, int(interval))
            self.status_label.text = f'[Desktop] Simülasyon başlatıldı → {api_url}'

    # ── Servis Durdur ────────────────────────────────────────────────────────
    def stop_service(self, *args):
        os.environ['MONITOR_STOP'] = '1'
        if platform == 'android':
            try:
                PythonService.stop()
            except Exception:
                pass
        self.status_label.text = '⏹ Servis durduruldu'
        self._log('Servis durduruldu.')

    # ── Log Yardımcısı ───────────────────────────────────────────────────────
    def _log(self, msg):
        import datetime
        ts  = datetime.datetime.now().strftime('%H:%M:%S')
        cur = self.log_label.text
        self.log_label.text = f'[{ts}] {msg}\n' + cur

    # ── Desktop Simülasyonu ──────────────────────────────────────────────────
    def _start_desktop_thread(self, api_url, interval):
        import threading

        def run():
            import time, requests, platform as _p, json
            os.environ.pop('MONITOR_STOP', None)
            while os.environ.get('MONITOR_STOP') != '1':
                payload = {
                    'device': _p.node(),
                    'os':     f'{_p.system()} {_p.release()}',
                    'cpu':    None,
                    'battery': None,
                    'timestamp': __import__('datetime').datetime.utcnow().isoformat()
                }
                try:
                    from plyer import battery
                    payload['battery'] = battery.status.get('percentage')
                except Exception:
                    pass
                try:
                    import psutil
                    payload['cpu']    = psutil.cpu_percent(interval=1)
                    payload['memory'] = psutil.virtual_memory().percent
                except Exception:
                    pass
                try:
                    r = requests.post(api_url, json=payload, timeout=5)
                    Clock.schedule_once(lambda dt, s=f'POST {r.status_code}': self._log(s), 0)
                except Exception as e:
                    Clock.schedule_once(lambda dt, s=f'Bağlantı hatası: {e}': self._log(s), 0)
                time.sleep(interval)

        t = threading.Thread(target=run, daemon=True)
        t.start()


# ── App ──────────────────────────────────────────────────────────────────────
class SystemMonitorApp(App):
    def build(self):
        return MonitorLayout()

    def on_pause(self):
        # Android'de arka plana geçişte uygulamayı kapat (servis devam eder)
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    SystemMonitorApp().run()
