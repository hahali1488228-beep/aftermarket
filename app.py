import os
import time
import random
import sqlite3
import threading
import logging
import json
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
PREFIXES = ["Golden", "Dark", "Cyber", "Mystic", "Royal", "Crystal", "Neon", "Shadow", "Ancient", "Legendary", "Frozen", "Electric", "Cosmic", "Lunar", "Solar", "Diamond", "Phantom", "Infernal", "Divine", "Cursed", "Eternal", "Void", "Astral", "Demonic", "Angelic", "Mechanical", "Organic", "Glitch", "Retro", "Future", "Steampunk", "Viking", "Samurai", "Ninja", "Pirate", "Alien", "Mutant", "Toxic", "Radioactive", "Glowing"]
OBJECTS = ["Dragon", "Tiger", "Crown", "Sword", "Cat", "Robot", "Ghost", "Phoenix", "Skull", "Wolf", "Gem", "Star", "Portal", "Mask", "Knight", "Treasure", "Planet", "Cactus", "Coconut", "Trophy", "Shield", "Bow", "Arrow", "Hammer", "Axe", "Potion", "Scroll", "Map", "Key", "Lock"]

NFT_POOL = [f"{p} {o}" for p in PREFIXES for o in OBJECTS] # 1200 NFT
RARITIES = [
    ("Обычный", 50, 150, 0.50),
    ("Редкий", 150, 400, 0.25),
    ("Эпический", 400, 1000, 0.15),
    ("Легендарный", 1000, 3000, 0.08),
    ("Мифический", 3000, 10000, 0.02)
]

def generate_random_nft():
    name = random.choice(NFT_POOL)
    rand = random.random()
    cumulative = 0
    for rarity, min_p, max_p, chance in RARITIES:
        cumulative += chance
        if rand <= cumulative:
            return name, rarity, random.randint(min_p, max_p)
    return name, "Обычный", 100

# ================= LANGUAGES =================
LANGUAGES = {
    "ru": {"welcome": "🎮 Добро пожаловать в MEGA BOT!", "games": "🎮 Игры", "profile": "👤 Профиль", "market": "💎 Маркет", "settings": "⚙️ Настройки", "back": "⬅️ Назад", "choose": "Выбери режим:", "nobal": "❌ Мало монет!"},
    "en": {"welcome": "🎮 Welcome to MEGA BOT!", "games": "🎮 Games", "profile": "👤 Profile", "market": "💎 Market", "settings": "⚙️ Settings", "back": "⬅️ Back", "choose": "Choose mode:", "nobal": "❌ Not enough coins!"}
}

def get_user(uid):
    return execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def register(message):
    uid = message.from_user.id
    username = message.from_user.username or "NoName"
    execute("INSERT OR IGNORE INTO users(id,username) VALUES(?,?)", (uid, username))
    execute("UPDATE users SET username=? WHERE id=?", (username, uid))

def add_balance(uid, amount):
    execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, uid))

def add_xp(uid, amount):
    execute("UPDATE users SET xp=xp+? WHERE id=?", (amount, uid))
    user = get_user(uid)
    execute("UPDATE users SET level=? WHERE id=?", ((user[3] // 1000) + 1, uid))

# ================= KEYBOARDS =================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 Игры", "👤 Профиль")
    kb.row("💎 Маркет", "🎁 Кейсы")
    kb.row("🏆 Топ", "⚙️ Настройки")
    return kb

def game_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [("🎰 Слоты", "slots"), ("🎲 Кубики", "dice"), ("🪙 Монетка", "coin"), ("🎯 Дартс", "dart"), ("🃏 Карты", "cards"), ("💣 Сапёр", "mines"), ("🧠 Викторина", "quiz"), ("🐉 Босс", "boss")]
    for title, callback in buttons: kb.add(types.InlineKeyboardButton(title, callback_data="game_" + callback))
    return kb

# ================= GAMES =================
def play_slots(chat_id, uid):
    user = get_user(uid)
    if user[2] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    add_balance(uid, -50)
    msg = bot.send_message(chat_id, "🎰 | ❔ | ❔ | ❔")
    for frame in ["🎰 | 🍒 | ❔ | ❔", "🎰 | ⭐ | 🍋 | ❔", "🎰 | 💎 | 🍒 | ⭐", "🎰 | 🔄 | 🔄 | 🔄"]:
        time.sleep(0.3)
        try: bot.edit_message_text(frame, chat_id, msg.message_id)
        except: pass
    res = [random.choice(["🍒", "🍋", "🍇", "⭐", "💎", "7️⃣"]) for _ in range(3)]
    if res == ["7️⃣"] * 3:
        reward = 500; add_balance(uid, reward); text = f"🏆 ДЖЕКПОТ! +{reward} 🪙"
    elif len(set(res)) == 1:
        reward = 150; add_balance(uid, reward); text = f"🔥 Три одинаковых! +{reward} 🪙"
    elif len(set(res)) == 2:
        reward = 50; add_balance(uid, reward); text = f"✨ Пара! +{reward} 🪙"
    else: text = "😢 Не повезло."
    bot.edit_message_text(f"🎰 {' | '.join(res)}\n\n{text}", chat_id, msg.message_id)

def play_dice(chat_id, uid):
    user = get_user(uid)
    if user[2] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    add_balance(uid, -50)
    msg = bot.send_message(chat_id, "🎲 Бросаем...")
    time.sleep(1)
    val = random.randint(1, 6)
    if val >= 4:
        add_balance(uid, 100); text = f"🎉 Выпало {val}! Победа! +100 🪙"
    else: text = f"😢 Выпало {val}. Проигрыш."
    bot.edit_message_text(text, chat_id, msg.message_id)

def play_coin(chat_id, uid):
    user = get_user(uid)
    if user[2] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    add_balance(uid, -50)
    res = random.choice(["Орёл 🦅", "Решка 🪙"])
    if "Орёл" in res: add_balance(uid, 100); text = "🎉 Орёл! Победа! +100 🪙"
    else: text = "😢 Решка. Проигрыш."
    bot.send_message(chat_id, f"🪙 Подбрасываем...\nВыпало: {res}\n\n{text}")

def play_dart(chat_id, uid):
    user = get_user(uid)
    if user[2] < 50:
        bot.send_message(chat_id, "❌ Нужно 50 монет!"); return
    add_balance(uid, -50)
    msg = bot.send_dice(chat_id, emoji="🎯")
    time.sleep(1)
    pts = msg.dice.value
    reward = pts * 20
    add_balance(uid, reward)
    bot.send_message(chat_id, f"🎯 Попадание: {pts}\n💰 Награда: {reward}")

def play_cards(chat_id, uid):
    cards = [("2", 2), ("3", 3), ("4", 4), ("5", 5), ("6", 6), ("7", 7), ("8", 8), ("9", 9), ("10", 10), ("J", 11), ("Q", 12), ("K", 13), ("A", 14)]
    f, s = random.sample(cards, 2)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬆️ Выше", callback_data=f"card_higher_{f[1]}_{s[1]}"), types.InlineKeyboardButton("⬇️ Ниже", callback_data=f"card_lower_{f[1]}_{s[1]}"))
    bot.send_message(chat_id, f"🃏 Первая карта: {f[0]}\nВторая будет выше или ниже?", reply_markup=kb)

def mines_game(chat_id, uid):
    kb = types.InlineKeyboardMarkup(row_width=3)
    for i in range(9): kb.insert(types.InlineKeyboardButton("❔", callback_data=f"mine_{i}"))
    bot.send_message(chat_id, "💣 Сапёр! Где мины?", reply_markup=kb)

def quiz_game(chat_id):
    q = random.choice([("Сколько будет 5×5?", ["20", "25", "30"], 1), ("Столица Франции?", ["Париж", "Рим", "Берлин"], 0), ("Сколько планет?", ["7", "8", "9"], 1)])
    kb = types.InlineKeyboardMarkup()
    for i, a in enumerate(q[1]): kb.add(types.InlineKeyboardButton(a, callback_data=f"quiz_{i}_{q[2]}"))
    bot.send_message(chat_id, "🧠 " + q[0], reply_markup=kb)

def boss_game(chat_id, uid):
    if random.randint(1, 100) > 50:
        add_balance(uid, 500); bot.send_message(chat_id, "🐉 БОСС ПОБЕЖДЁН! +500 🪙")
    else: bot.send_message(chat_id, "🐉 Босс победил тебя...")

# ================= CASES =================
CASES = {
    "common": (100, 1), "rare": (300, 2), "epic": (1000, 3), "legend": (5000, 5)
}

def cases_menu(chat_id):
    kb = types.InlineKeyboardMarkup()
    for name, cost in [("Обычный (100)", "common"), ("Редкий (300)", "rare"), ("Эпический (1000)", "epic"), ("Легендарный (5000)", "legend")]:
        kb.add(types.InlineKeyboardButton(name, callback_data="case_" + cost))
    bot.send_message(chat_id, "🎁 Выбери кейс:", reply_markup=kb)

def open_case(uid, chat_id, ctype):
    if ctype not in CASES: return
    cost, count = CASES[ctype]
    user = get_user(uid)
    if user[2] < cost:
        bot.send_message(chat_id, "❌ Мало монет!"); return
    add_balance(uid, -cost)
    text = f"🎁 Ты открыл {ctype} кейс!\n\n"
    for _ in range(count):
        name, rarity, price = generate_random_nft()
        execute("INSERT INTO inventory(owner,name,rarity,price) VALUES(?,?,?,?)", (uid, name, rarity, price))
        text += f"✨ {name} ({rarity}) — {price} 🪙\n"
    bot.send_message(chat_id, text)

# ================= MARKET =================
def market_menu(chat_id):
    items = execute("SELECT market.id, inventory.name, inventory.rarity, market.price, users.username FROM market JOIN inventory ON inventory.id=market.nft_id JOIN users ON users.id=inventory.owner LIMIT 10").fetchall()
    if not items:
        bot.send_message(chat_id, "💎 Маркет пуст."); return
    for item in items:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🛒 Купить", callback_data=f"buy_{item[0]}"))
        bot.send_message(chat_id, f"💎 {item[1]}\n⭐ {item[2]}\n💰 {item[3]}\n👤 @{item[4]}", reply_markup=kb)

# ================= INVENTORY & SELL =================
def my_inventory(uid, chat_id):
    items = execute("SELECT id,name,rarity,price FROM inventory WHERE owner=? AND listed=0", (uid,)).fetchall()
    if not items:
        bot.send_message(chat_id, "📦 Инвентарь пуст."); return
    for item in items:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💸 Продать", callback_data=f"sell_{item[0]}_{item[3]}"))
        bot.send_message(chat_id, f"#{item[0]} — {item[1]}\n⭐ {item[2]} | 💰 {item[3]}", reply_markup=kb)

# ================= DAILY & PROFILE =================
def daily(uid, chat_id):
    today = time.strftime("%Y-%m-%d")
    user = get_user(uid)
    if user[8] == today:
        bot.send_message(chat_id, "⏳ Уже брал сегодня!"); return
    reward = random.randint(200, 500)
    execute("UPDATE users SET balance=balance+?,daily=? WHERE id=?", (reward, today, uid))
    bot.send_message(chat_id, f"🎁 Ежедневный бонус: +{reward} 🪙")

def profile(uid, chat_id):
    user = get_user(uid)
    nfts = execute("SELECT COUNT(*) FROM inventory WHERE owner=?", (uid,)).fetchone()[0]
    stats = execute("SELECT games,wins FROM stats WHERE user_id=?", (uid,)).fetchone()
    games, wins = stats or (0, 0)
    bot.send_message(chat_id, f"👤 ПРОФИЛЬ\n\n🆔 ID: `{uid}`\n💰 Баланс: {user[2]}\n⭐ Уровень: {user[4]}\n💎 NFT: {nfts}\n🎮 Игр: {games}\n🏆 Побед: {wins}", parse_mode="Markdown")

# ================= ADMIN =================
def admin_menu(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    kb.add(types.InlineKeyboardButton("🎁 Выдать монеты (по ID)", callback_data="admin_give"))
    bot.send_message(chat_id, "🛠️ Админка:", reply_markup=kb)

# ================= BOT HANDLERS =================
@bot.message_handler(commands=["start"])
def start(message):
    register(message)
    bot.send_message(message.chat.id, "🎮 MEGA BOT 3.0\n\nБаланс: 1000 🪙", reply_markup=main_menu())

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    msg = bot.send_message(message.chat.id, "🔐 Код:")
    bot.register_next_step_handler(msg, check_admin)

def check_admin(message):
    if message.text == ADMIN_CODE:
        execute("UPDATE users SET admin=1 WHERE id=?", (message.from_user.id,))
        admin_menu(message.chat.id)
    else: bot.send_message(message.chat.id, "❌ Неверно!")

@bot.message_handler(content_types=["text"])
def text_handler(message):
    uid = message.from_user.id
    chat = message.chat.id
    txt = message.text
    register(message)
    user = get_user(uid)
    if user[7]: return
    
    if txt == "🎮 Игры": bot.send_message(chat, "Выбери:", reply_markup=game_menu())
    elif txt == "👤 Профиль": profile(uid, chat)
    elif txt == "💎 Маркет": market_menu(chat)
    elif txt == "🎁 Кейсы": cases_menu(chat)
    elif txt == "⚙️ Настройки": bot.send_message(chat, "В разработке...")
    elif txt == "🏆 Топ": 
        top = execute("SELECT username,balance FROM users ORDER BY balance DESC LIMIT 5").fetchall()
        t = "🏆 ТОП:\n" + "\n".join([f"{i+1}. @{u[0]} — {u[1]}" for i, u in enumerate(top)])
        bot.send_message(chat, t)
    elif txt == "🎁 Бонус": daily(uid, chat)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    chat = call.message.chat.id
    d = call.data
    if d == "game_slots": play_slots(chat, uid)
    elif d == "game_dice": play_dice(chat, uid)
    elif d == "game_coin": play_coin(chat, uid)
    elif d == "game_dart": play_dart(chat, uid)
    elif d == "game_cards": play_cards(chat, uid)
    elif d == "game_mines": mines_game(chat, uid)
    elif d == "game_quiz": quiz_game(chat)
    elif d == "game_boss": boss_game(chat, uid)
    elif d.startswith("case_"): open_case(uid, chat, d.split("_")[1])
    elif d.startswith("sell_"):
        _, nid, price = d.split("_")
        execute("UPDATE inventory SET listed=1 WHERE id=?", (nid,))
        execute("INSERT INTO market(seller,nft_id,price) VALUES(?,?,?)", (uid, nid, price))
        bot.answer_callback_query(call.id, "✅ Выставлено на маркет!")
    elif d.startswith("buy_"):
        mid = d.split("_")[1]
        item = execute("SELECT * FROM market WHERE id=?", (mid,)).fetchone()
        if not item: return
        seller, nft_id, price = item[1], item[2], item[3]
        buyer = get_user(uid)
        if buyer[2] < price:
            bot.answer_callback_query(call.id, "❌ Мало монет!", show_alert=True); return
        add_balance(uid, -price)
        add_balance(seller, price)
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
