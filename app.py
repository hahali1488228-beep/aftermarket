import os
import threading
from flask import Flask

# --- КОД БОТА ---
import urllib.request
import urllib.parse
import json
import time

TOKEN = os.environ.get('TELEGRAM_TOKEN', '9133073082:AAEMW6Uv6S2wvcEII7xlXmUNp4KdHsRqpRE')
API_URL = f"https://api.telegram.org/bot{TOKEN}/"
ADMIN_CODE = "DD29KL"

def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def api_request(method, params=None):
    url = API_URL + method
    data = urllib.parse.urlencode(params).encode('utf-8') if params else None
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode('utf-8'))
    except Exception as e: return None

def send_msg(cid, text, markup=None):
    p = {'chat_id': cid, 'text': text, 'parse_mode': 'Markdown'}
    if markup: p['reply_markup'] = json.dumps(markup)
    api_request('sendMessage', p)

def edit_msg(cid, mid, text, markup=None):
    p = {'chat_id': cid, 'message_id': mid, 'text': text, 'parse_mode': 'Markdown'}
    if markup: p['reply_markup'] = json.dumps(markup)
    api_request('editMessageText', p)

def run_bot():
    print("🚀 Бот запущен!")
    last_id = 0
    while True:
        try:
            upd = api_request('getUpdates', {'offset': last_id + 1, 'timeout': 10})
            if upd and upd.get('ok'):
                for u in upd['result']:
                    last_id = u['update_id']
                    if 'message' in u:
                        m = u['message']; cid = m['chat']['id']; txt = m.get('text', '')
                        if txt == '/start':
                            send_msg(cid, "👋 Привет! Это NFT Маркет. Бот работает стабильно! 🚀")
                        elif txt == ADMIN_CODE:
                            send_msg(cid, "👑 Ты получил права админа!")
        except Exception as e:
            time.sleep(1)

# --- ОБЕРТКА ДЛЯ RENDER ---
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is running", 200

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
