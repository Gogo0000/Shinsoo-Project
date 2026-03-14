# server/app.py — Flask API (Sunucu Tarafı)
# Kurulum: pip install flask
# Çalıştırma: python server/app.py

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# Gelen raporları bellekte tut (production'da veritabanı kullanın)
reports = []
MAX_REPORTS = 1000


# ── POST /api/report ─────────────────────────────────────────────────────────

@app.route('/api/report', methods=['POST'])
def receive_report():
    """Android cihazdan gelen sistem verisini kabul eder."""
    if not request.is_json:
        return jsonify({'error': 'Content-Type application/json olmalı'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Boş veri'}), 400

    # Sunucu tarafı zaman damgası ekle
    data['server_received_at'] = datetime.utcnow().isoformat() + 'Z'
    data['client_ip']          = request.remote_addr

    reports.append(data)
    if len(reports) > MAX_REPORTS:
        reports.pop(0)

    _log(f"[RAPOR] {data.get('client_ip')} | "
         f"cihaz={data.get('device', {}).get('model', '?')} | "
         f"batarya={data.get('battery', {}).get('level', '?')}%")

    return jsonify({'status': 'ok', 'received': data['server_received_at']}), 200


# ── GET /api/reports ─────────────────────────────────────────────────────────

@app.route('/api/reports', methods=['GET'])
def list_reports():
    """Son N raporu JSON olarak döner."""
    limit = int(request.args.get('limit', 50))
    return jsonify(reports[-limit:])


# ── GET /api/latest ──────────────────────────────────────────────────────────

@app.route('/api/latest', methods=['GET'])
def latest_report():
    """En son raporu döner."""
    if not reports:
        return jsonify({'error': 'Henüz rapor yok'}), 404
    return jsonify(reports[-1])


# ── GET / — Basit Web Paneli ─────────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Ham HTML ile basit bir izleme paneli."""
    html = '''
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sistem İzleme Paneli</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
    h1 { color: #38bdf8; margin-bottom: 20px; }
    .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    .card h2 { font-size: 14px; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
    .stat { display: flex; justify-content: space-between; padding: 6px 0;
            border-bottom: 1px solid #334155; }
    .stat:last-child { border-bottom: none; }
    .val { font-weight: 600; color: #38bdf8; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 12px; }
    .green { background: #166534; color: #86efac; }
    .yellow { background: #854d0e; color: #fde047; }
    .red { background: #7f1d1d; color: #fca5a5; }
    button { background: #0ea5e9; color: #fff; border: none; padding: 10px 24px;
             border-radius: 8px; cursor: pointer; font-size: 14px; margin-top: 16px; }
    button:hover { background: #0284c7; }
    pre { background: #0f172a; border-radius: 8px; padding: 12px; overflow-x: auto;
          font-size: 12px; color: #94a3b8; max-height: 300px; overflow-y: auto; }
    #ts { color: #475569; font-size: 13px; margin-bottom: 12px; }
  </style>
</head>
<body>
  <h1>🖥️ Sistem İzleme Paneli</h1>
  <p id="ts">Son güncelleme: —</p>
  <div id="cards" class="grid"></div>
  <pre id="raw">Yükleniyor…</pre>
  <button onclick="fetchData()">🔄 Yenile</button>

  <script>
    async function fetchData() {
      try {
        const res  = await fetch('/api/latest');
        if (!res.ok) { document.getElementById('raw').textContent = 'Henüz veri yok.'; return; }
        const d    = await res.json();
        document.getElementById('ts').textContent = 'Son güncelleme: ' + (d.server_received_at || '—');
        document.getElementById('raw').textContent = JSON.stringify(d, null, 2);

        const dev = d.device || {};
        const bat = d.battery || {};
        const mem = d.memory  || {};
        const cpu = d.cpu     || {};

        const batLevel = bat.level ?? '—';
        const batBadge = batLevel >= 50 ? 'green' : batLevel >= 20 ? 'yellow' : 'red';

        document.getElementById('cards').innerHTML = `
          <div class="card">
            <h2>📱 Cihaz</h2>
            <div class="stat"><span>Marka</span><span class="val">${dev.brand || '—'}</span></div>
            <div class="stat"><span>Model</span><span class="val">${dev.model || '—'}</span></div>
            <div class="stat"><span>Android</span><span class="val">${dev.release || '—'} (SDK ${dev.sdk || '—'})</span></div>
            <div class="stat"><span>IP</span><span class="val">${d.client_ip || '—'}</span></div>
          </div>
          <div class="card">
            <h2>🔋 Batarya</h2>
            <div class="stat"><span>Seviye</span>
              <span class="val"><span class="badge ${batBadge}">%${batLevel}</span></span></div>
            <div class="stat"><span>Şarj</span>
              <span class="val">${bat.charging ? '⚡ Evet' : 'Hayır'}</span></div>
            <div class="stat"><span>Voltaj</span>
              <span class="val">${bat.voltage ? bat.voltage + ' mV' : '—'}</span></div>
          </div>
          <div class="card">
            <h2>💾 Bellek</h2>
            <div class="stat"><span>Toplam</span><span class="val">${mem.total_mb || '—'} MB</span></div>
            <div class="stat"><span>Kullanılan</span><span class="val">${mem.used_mb || '—'} MB</span></div>
            <div class="stat"><span>Boş</span><span class="val">${mem.avail_mb || '—'} MB</span></div>
            <div class="stat"><span>Kullanım</span><span class="val">%${mem.used_pct || '—'}</span></div>
          </div>
          <div class="card">
            <h2>⚙️ CPU</h2>
            <div class="stat"><span>Kullanım</span><span class="val">%${cpu.usage_pct ?? '—'}</span></div>
          </div>`;
      } catch (e) {
        document.getElementById('raw').textContent = 'Hata: ' + e.message;
      }
    }

    fetchData();
    setInterval(fetchData, 10000); // 10 saniyede bir otomatik yenile
  </script>
</body>
</html>'''
    return html


# ── Yardımcı ─────────────────────────────────────────────────────────────────

def _log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')


# ── Başlat ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'Flask API başlatılıyor → http://0.0.0.0:{port}')
    print('Panel: http://localhost:5000/')
    app.run(host='0.0.0.0', port=port, debug=True)
