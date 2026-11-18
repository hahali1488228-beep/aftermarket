import os
import threading
from flask import Flask
import urllib.request
import urllib.parse
import json
import time
import random

# --- НАСТРОЙКИ ---
TOKEN = os.environ.get('TELEGRAM_TOKEN', '9133073082:AAEMW6Uv6S2wvcEII7xlXmUNp4KdHsRqpRE')
API_URL = f"https://api.telegram.org/bot{TOKEN}/"
ADMIN_CODE = "DD29KL"

DB_USERS = "users.json"
DB_NFTS = "nfts.json"
DB_SETTINGS = "settings.json"

CHESTS = [
    {"id": "wood", "name": "🪵 Деревянный", "price": 50, "min": 10, "max": 80, "nft_chance": 0.05},
    {"id": "iron", "name": "⛓️ Железный", "price": 150, "min": 50, "max": 200, "nft_chance": 0.10},
    {"id": "gold", "name": "🪙 Золотой", "price": 400, "min": 150, "max": 600, "nft_chance": 0.20},
    {"id": "diamond", "name": "💎 Алмазный", "price": 1000, "min": 500, "max": 1500, "nft_chance": 0.30},
    {"id": "emerald", "name": "🟢 Изумрудный", "price": 2500, "min": 1000, "max": 4000, "nft_chance": 0.40},
    {"id": "ruby", "name": "🔴 Рубиновый", "price": 5000, "min": 2000, "max": 8000, "nft_chance": 0.50},
    {"id": "obsidian", "name": "🌑 Обсидиановый", "price": 10000, "min": 5000, "max": 15000, "nft_chance": 0.60},
    {"id": "mythic", "name": "🦄 Мифический", "price": 25000, "min": 10000, "max": 40000, "nft_chance": 0.75},
    {"id": "legend", "name": "👑 Легендарный", "price": 50000, "min": 20000, "max": 100000, "nft_chance": 0.85},
    {"id": "god", "name": "🌌 Божественный", "price": 100000, "min": 50000, "max": 250000, "nft_chance": 0.99}
]

NFT_NAMES = ["Кот", "Пёс", "Ракета", "Пицца", "Космос", "Алмаз", "Корона", "Меч", "Щит", "Звезда", "Планета", "Дракон", "Единорог", "Призрак", "Робот"]
NFT_RARITY = ["Обычный", "Редкий", "Эпический", "Легендарный", "Мифический"]

def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

users = load_data(DB_USERS, {})
nfts = load_data(DB_NFTS, [])
settings = load_data(DB_SETTINGS, {"banned": []})

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

def ans_cb(cid, text=None):
    p = {'callback_query_id': cid}
    if text: p['text'] = text; p['show_alert'] = True
    api_request('answerCallbackQuery', p)

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"balance": 500, "inv": [], "is_admin": False}
        save_data(DB_USERS, users)
    return users[uid]

def main_menu(uid):
    kb = [
        [{"text": "🏪 Маркет", "callback_data": "market"}, {"text": "👤 Профиль", "callback_data": "profile"}],
        [{"text": "🎰 Казино", "callback_data": "casino"}, {"text": "🎁 Сундуки", "callback_data": "chests"}],
        [{"text": "📢 Канал", "url": "https://t.me/marketnft111"}]
    ]
    if users.get(str(uid), {}).get("is_admin"): kb.append([{"text": "👑 Админка", "callback_data": "admin_panel"}])
    return {"inline_keyboard": kb}

def casino_menu():
    return {"inline_keyboard": [
        [{"text": "🔴 Рулетка", "callback_data": "g_roulette"}],
        [{"text": "🍒 Слоты", "callback_data": "g_slots"}],
        [{"text": "🎲 Кубик", "callback_data": "g_dice"}],
        [{"text": "🪙 Монетка", "callback_data": "g_coin"}],
        [{"text": "« Назад", "callback_data": "back_home"}]
    ]}

def chests_menu():
    kb = []
    for c in CHESTS:
        kb.append([{"text": f"{c['name']} - {c['price']} 🪙", "callback_data": f"buy_{c['id']}"}])
    kb.append([{"text": "« Назад", "callback_data": "back_home"}])
    return {"inline_keyboard": kb}

def run_bot():
    print("🚀 Казино-Маркет запущен!")
    last_id = 0
    while True:
        try:
            upd = api_request('getUpdates', {'offset': last_id + 1, 'timeout': 10})
            if upd and upd.get('ok'):
                for u in upd['result']:
                    last_id = u['update_id']
                    
                    if 'message' in u:
                        m = u['message']; cid = m['chat']['id']; uid = m['from']['id']; txt = m.get('text', '')
                        username = m['from'].get('username', 'без_юзернейма')
                        user = get_user(uid)
                        
                        if str(uid) in settings["banned"]: send_msg(cid, "⛔ Вы забанены."); continue
                        
                        if txt == '/start':
                            send_msg(cid, f"👋 Привет, @{username}!\n\nТвой баланс: *{user['balance']} 🪙*\nВыбирай, чем займемся?", main_menu(uid))
                        elif txt == ADMIN_CODE:
                            users[str(uid)]["is_admin"] = True; save_data(DB_USERS, users)
                            send_msg(cid, "👑 Админка открыта!", main_menu(uid))
                        
                    elif 'callback_query' in u:
                        c = u['callback_query']; cid = c['message']['chat']['id']; mid = c['message']['message_id']; uid = c['from']['id']; d = c['data']
                        user = get_user(uid)
                        
                        if d == "back_home": ans_cb(c['id']); edit_msg(cid, mid, "🏠 Главное меню", main_menu(uid))
                        
                        elif d == "profile":
                            ans_cb(c['id'])
                            txt = f"👤 **Профиль**\n\n🆔 ID: `{uid}`\n💰 Баланс: *{user['balance']} 🪙*\n📦 Инвентарь: {len(user.get('inv', []))} NFT\n\n"
                            if user.get('inv'):
                                txt += "**Твои NFT:**\n"
                                for nft in user['inv'][:5]: # Показываем первые 5
                                    txt += f"• {nft['name']} ({nft['rarity']})\n"
                            edit_msg(cid, mid, txt, main_menu(uid))
                        
                        elif d == "casino": ans_cb(c['id']); edit_msg(cid, mid, "🎰 **Казино**", casino_menu())
                        elif d == "chests": ans_cb(c['id']); edit_msg(cid, mid, "🎁 **Сундуки**", chests_menu())
                        
                        # --- ИГРЫ ---
                        elif d.startswith("g_"):
                            game = d.split("_")[1]
                            bet = 100
                            if user['balance'] < bet:
                                ans_cb(c['id'], "❌ Нужно 100 монет!", True); continue
                            
                            win = random.choice([True, False])
                            if win:
                                users[str(uid)]['balance'] += bet
                                txt = f"🎉 Победа! Выиграл {bet} 🪙"
                            else:
                                users[str(uid)]['balance'] -= bet
                                txt = f"😢 Проигрыш... Потерял {bet} 🪙"
                            
                            save_data(DB_USERS, users)
                            ans_cb(c['id'], "Игра окончена!", True)
                            edit_msg(cid, mid, txt, casino_menu())
                            
                        # --- СУНДУКИ ---
                        elif d.startswith("buy_"):
                            chest_id = d.replace("buy_", "")
                            chest = next((ch for ch in CHESTS if ch['id'] == chest_id), None)
                            if not chest: continue
                            
                            if user['balance'] < chest['price']:
                                ans_cb(c['id'], "❌ Недостаточно монет!", True); continue
                            
                            users[str(uid)]['balance'] -= chest['price']
                            save_data(DB_USERS, users)
                            
                            if random.random() < chest['nft_chance']:
                                nft_name = random.choice(NFT_NAMES)
                                nft_rarity = random.choice(NFT_RARITY)
                                nft_price = random.randint(chest['price']*2, chest['price']*5)
                                
                                new_nft = {"id": len(nfts)+1, "owner": uid, "name": nft_name, "rarity": nft_rarity, "price": nft_price}
                                nfts.append(new_nft)
                                save_data(DB_NFTS, nfts)
                                
                                if 'inv' not in users[str(uid)]: users[str(uid)]['inv'] = []
                                users[str(uid)]['inv'].append(new_nft)
                                save_data(DB_USERS, users)
                                
                                txt = f"🎉 **ДЖЕКПОТ!**\n\nТы выбил NFT:\n✨ **{nft_name}** ({nft_rarity})\n💰 Цена: {nft_price} 🪙"
                            else:
                                coins = random.randint(chest['min'], chest['max'])
                                users[str(uid)]['balance'] += coins
                                save_data(DB_USERS, users)
                                txt = f"📦 Ты открыл **{chest['name']}**...\n\nВнутри: +{coins} 🪙"
                            
                            ans_cb(c['id'], "Сундук открыт!", True)
                            edit_msg(cid, mid, txt, main_menu(uid))
                            
                        elif d == "admin_panel":
                            if not users[str(uid)].get("is_admin"): continue
                            kb = {"inline_keyboard": [[{"text": "🚫 Бан", "callback_data": "admin_ban"}, {"text": "🗑️ Удалить лот", "callback_data": "admin_del"}], [{"text": "Назад", "callback_data": "back_home"}]]}
                            edit_msg(cid, mid, "👑 **Админка**", kb)
                            
                        elif d == "admin_ban":
                            if not users[str(uid)].get("is_admin"): continue
                            user_states[uid] = {"step": "wait_ban"}
                            edit_msg(cid, mid, "Введи ID для бана:")
                            
                        elif d == "admin_del":
                            if not users[str(uid)].get("is_admin"): continue
                            user_states[uid] = {"step": "wait_del"}
                            edit_msg(cid, mid, "Введи ID лота для удаления:")

        except Exception as e:
            print(f"Loop Error: {e}")

# --- FLASK ---
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is running", 200

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
