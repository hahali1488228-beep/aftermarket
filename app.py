import os
import time
import random
import sqlite3
import threading
import logging
from flask import Flask
import telebot
from telebot import types

# ================= CONFIG =================
TOKEN = os.getenv("TELEGRAM_TOKEN", "9133073082:AAEMW6Uv6S2wvcEII7xlXmUNp4KdHsRqpRE")
ADMIN_CODE = os.getenv("ADMIN_CODE", "DD29KL")

bot = telebot.TeleBot(TOKEN)
DB_LOCK = threading.RLock()
logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================
db = sqlite3.connect("mega_bot.db", check_same_thread=False)

def execute(query, params=()):
    with DB_LOCK:
        cur = db.execute(query, params)
        db.commit()
        return cur

def init_db():
    execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 1000, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, lang TEXT DEFAULT 'ru', admin INTEGER DEFAULT 0, banned INTEGER DEFAULT 0, daily TEXT DEFAULT '')")
    execute("CREATE TABLE IF NOT EXISTS inventory(id INTEGER PRIMARY KEY AUTOINCREMENT, owner INTEGER, name TEXT, rarity TEXT, price INTEGER, listed INTEGER DEFAULT 0)")
    execute("CREATE TABLE IF NOT EXISTS market(id INTEGER PRIMARY KEY AUTOINCREMENT, seller INTEGER, nft_id INTEGER, price INTEGER)")
    execute("CREATE TABLE IF NOT EXISTS stats(user_id INTEGER PRIMARY KEY, games INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, jackpots INTEGER DEFAULT 0)")
    execute("CREATE TABLE IF NOT EXISTS achievements(user_id INTEGER, name TEXT, UNIQUE(user_id, name))")

init_db()

# ================= 1000+ NFT GENERATION =================
PREFIXES = ["Golden", "Dark", "Cyber", "Mystic", "Royal", "Crystal", "Neon", "Shadow", "Ancient", "Legendary", "Frozen", "Electric", "Cosmic", "Lunar", "Solar", "Diamond", "Phantom", "Infernal", "Divine", "Cursed", "Eternal", "Void", "Astral", "Demonic", "Angelic", "Mechanical", "Organic", "Glitch", "Retro", "Future"]
OBJECTS = ["Dragon", "Tiger", "Crown", "Sword", "Cat", "Robot", "Ghost", "Phoenix", "Skull", "Wolf", "Gem", "Star", "Portal", "Mask", "Knight", "Treasure", "Planet", "Cactus", "Coconut", "Trophy", "Shield", "Bow", "Arrow", "Hammer", "Axe", "Potion", "Scroll", "Map", "Key", "Lock"]

NFT_POOL = [f"{p} {o}" for p in PREFIXES for o in OBJECTS] 
RARITIES = [("Обычный", 50, 150), ("Редкий", 150, 400), ("Эпический", 400, 1000), ("Легендарный", 1000, 3000), ("Мифический", 3000, 10000)]

def generate_random_nft():
    name = random.choice(NFT_POOL)
    rarity, min_p, max_p = random.choice(RARITIES)
    return name, rarity, random.randint(min_p, max_p)

# ================= GAME LOGIC =================
SYMBOLS = ["🍒", "🍋", "🍇", "⭐", "💎", "7️⃣"]

def play_slots(chat_id, uid):
    user = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not user or user[0] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    execute("UPDATE users SET balance=balance-50 WHERE id=?", (uid,))
    
    msg = bot.send_message(chat_id, "🎰 | ❔ | ❔ | ❔")
    for frame in ["🎰 | 🍒 | ❔ | ❔", "🎰 | ⭐ | 🍋 | ❔", "🎰 | 💎 | 🍒 | ⭐", "🎰 | 🔄 | 🔄 | 🔄"]:
        time.sleep(0.4)
        try: bot.edit_message_text(frame, chat_id, msg.message_id)
        except: pass
        
    res = [random.choice(SYMBOLS) for _ in range(3)]
    reward = 0
    text = "😅 Не повезло!"
    
    if res == ["7️⃣", "7️⃣", "7️⃣"]:
        reward = 500; text = "🏆 ДЖЕКПОТ 777!"
    elif len(set(res)) == 1:
        reward = 150; text = "🔥 ТРИ ОДИНАКОВЫХ!"
    elif len(set(res)) == 2:
        reward = 50; text = "✨ ПАРА!"
        
    if reward:
        execute("UPDATE users SET balance=balance+? WHERE id=?", (reward, uid))
        execute("INSERT OR IGNORE INTO stats(user_id) VALUES(?)", (uid,))
        execute("UPDATE stats SET wins=wins+1 WHERE user_id=?", (uid,))
        
    bot.edit_message_text(f"🎰 {' | '.join(res)}\n\n{text}\n💰 Выигрыш: {reward}", chat_id, msg.message_id)

def play_dice(chat_id, uid):
    user = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not user or user[0] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    execute("UPDATE users SET balance=balance-50 WHERE id=?", (uid,))
    
    msg = bot.send_message(chat_id, "🎲 Бросаем...")
    time.sleep(1)
    val = random.randint(1, 6)
    if val >= 4:
        execute("UPDATE users SET balance=balance+100 WHERE id=?", (uid,))
        bot.edit_message_text(f"🎉 Выпало {val}! Победа! +100 🪙", chat_id, msg.message_id)
    else:
        bot.edit_message_text(f"😢 Выпало {val}. Проигрыш.", chat_id, msg.message_id)

def play_coin(chat_id, uid):
    user = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not user or user[0] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    execute("UPDATE users SET balance=balance-50 WHERE id=?", (uid,))
    res = random.choice(["Орёл 🦅", "Решка 🪙"])
    if "Орёл" in res:
        execute("UPDATE users SET balance=balance+100 WHERE id=?", (uid,))
        bot.send_message(chat_id, f"🪙 Выпало: {res}\n\n🎉 Победа! +100 🪙")
    else:
        bot.send_message(chat_id, f"🪙 Выпало: {res}\n\n😢 Проигрыш.")

def play_dart(chat_id, uid):
    user = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not user or user[0] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    execute("UPDATE users SET balance=balance-50 WHERE id=?", (uid,))
    msg = bot.send_dice(chat_id, emoji="🎯")
    time.sleep(1)
    pts = msg.dice.value
    reward = pts * 20
    execute("UPDATE users SET balance=balance+? WHERE id=?", (reward, uid))
    bot.send_message(chat_id, f"🎯 Попадание: {pts}\n💰 Награда: {reward}")

# ================= CASES & MARKET =================
CASES = {"common": (100, 1), "rare": (300, 2), "epic": (1000, 3), "legend": (5000, 5)}

def cases_menu(chat_id):
    kb = types.InlineKeyboardMarkup()
    for name, cost in [("Обычный (100)", "common"), ("Редкий (300)", "rare"), ("Эпический (1000)", "epic"), ("Легендарный (5000)", "legend")]:
        kb.add(types.InlineKeyboardButton(name, callback_data="case_" + cost))
    bot.send_message(chat_id, "🎁 Выбери кейс:", reply_markup=kb)

def open_case(uid, chat_id, ctype):
    if ctype not in CASES: return
    cost, count = CASES[ctype]
    user = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if user[0] < cost:
        bot.send_message(chat_id, "❌ Мало монет!"); return
    execute("UPDATE users SET balance=balance-? WHERE id=?", (cost, uid))
    
    text = f"🎁 Ты открыл {ctype} кейс!\n\n"
    for _ in range(count):
        name, rarity, price = generate_random_nft()
        execute("INSERT INTO inventory(owner,name,rarity,price) VALUES(?,?,?,?)", (uid, name, rarity, price))
        text += f"✨ {name} ({rarity}) — {price} 🪙\n"
    bot.send_message(chat_id, text)

def my_inventory(uid, chat_id):
    items = execute("SELECT id,name,rarity,price FROM inventory WHERE owner=? AND listed=0", (uid,)).fetchall()
    if not items:
        bot.send_message(chat_id, "📦 Инвентарь пуст."); return
    for item in items:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💸 Продать", callback_data=f"sell_{item[0]}_{item[3]}"))
        bot.send_message(chat_id, f"#{item[0]} — {item[1]}\n⭐ {item[2]} | 💰 {item[3]}", reply_markup=kb)

def market_menu(chat_id):
    items = execute("SELECT market.id, inventory.name, inventory.rarity, market.price FROM market JOIN inventory ON inventory.id=market.nft_id LIMIT 10").fetchall()
    if not items:
        bot.send_message(chat_id, "💎 Маркет пуст."); return
    for item in items:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🛒 Купить", callback_data=f"buy_{item[0]}"))
        bot.send_message(chat_id, f"💎 {item[1]}\n⭐ {item[2]}\n💰 {item[3]}", reply_markup=kb)

# ================= KEYBOARDS =================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 Игры", "👤 Профиль")
    kb.row("💎 Маркет", "🎁 Кейсы")
    kb.row("🎒 Инвентарь", "🎁 Бонус")
    return kb

def game_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for t, c in [("🎰 Слоты", "slots"), ("🎲 Кубики", "dice"), ("🪙 Монетка", "coin"), ("🎯 Дартс", "dart")]:
        kb.add(types.InlineKeyboardButton(t, callback_data="game_" + c))
    return kb

# ================= HANDLERS =================
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    execute("INSERT OR IGNORE INTO users(id,username) VALUES(?,?)", (uid, message.from_user.username or "User"))
    bot.send_message(message.chat.id, "🎮 MEGA BOT\n\nБаланс: 1000 🪙", reply_markup=main_menu())

@bot.message_handler(content_types=["text"])
def text_handler(message):
    uid = message.from_user.id
    chat = message.chat.id
    txt = message.text
    
    if txt == "🎮 Игры": bot.send_message(chat, "Выбери игру:", reply_markup=game_menu())
    elif txt == "👤 Профиль":
        u = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
        bot.send_message(chat, f"👤 Профиль\n🆔 `{uid}`\n💰 Баланс: {u[0]}", parse_mode="Markdown")
    elif txt == "💎 Маркет": market_menu(chat)
    elif txt == "🎁 Кейсы": cases_menu(chat)
    elif txt == "🎒 Инвентарь": my_inventory(uid, chat)
    elif txt == "🎁 Бонус":
        execute("UPDATE users SET balance=balance+200 WHERE id=?", (uid,))
        bot.send_message(chat, "🎁 Бонус получен: +200 🪙")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    chat = call.message.chat.id
    d = call.data
    if d == "game_slots": play_slots(chat, uid)
    elif d == "game_dice": play_dice(chat, uid)
    elif d == "game_coin": play_coin(chat, uid)
    elif d == "game_dart": play_dart(chat, uid)
    elif d.startswith("case_"): open_case(uid, chat, d.split("_")[1])
    elif d.startswith("sell_"):
        _, nid, price = d.split("_")
        execute("UPDATE inventory SET listed=1 WHERE id=?", (nid,))
        execute("INSERT INTO market(seller,nft_id,price) VALUES(?,?,?)", (uid, nid, price))
        bot.answer_callback_query(call.id, "✅ Выставлено!")
    elif d.startswith("buy_"):
        mid = d.split("_")[1]
        item = execute("SELECT * FROM market WHERE id=?", (mid,)).fetchone()
        if not item: return
        seller, nft_id, price = item[1], item[2], item[3]
        buyer = execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
        if buyer[0] < price:
            bot.answer_callback_query(call.id, "❌ Мало монет!", show_alert=True); return
        execute("UPDATE users SET balance=balance-? WHERE id=?", (price, uid))
        execute("UPDATE users SET balance=balance+? WHERE id=?", (price, seller))
        execute("UPDATE inventory SET owner=? WHERE id=?", (uid, nft_id))
        execute("DELETE FROM market WHERE id=?", (mid,))
        bot.answer_callback_query(call.id, "✅ Куплено!")

# ================= FLASK =================
app = Flask(__name__)
@app.route('/')
def health(): return "Bot Running"

def run_bot(): bot.infinity_polling()
if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
