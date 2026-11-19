
# ============================================================
#                 MEGA TELEGRAM BOT 2.0
#        GAMES • NFT • MARKET • PROFILE • ADMIN
# ============================================================

import os
import time
import random
import sqlite3
import threading
import logging
import html

import telebot
from telebot import types

# ================= CONFIG =================

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CODE = os.getenv("ADMIN_CODE")

if not TOKEN or not ADMIN_CODE:
    raise RuntimeError("Set TELEGRAM_TOKEN and ADMIN_CODE!")

bot = telebot.TeleBot(TOKEN)
DB_LOCK = threading.RLock()

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================

db = sqlite3.connect(
    "mega_bot.db",
    check_same_thread=False
)

def execute(query, params=()):
    with DB_LOCK:
        cur = db.execute(query, params)
        db.commit()
        return cur

def init_db():
    execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '',
        balance INTEGER DEFAULT 500,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        language TEXT DEFAULT 'ru',
        decoration TEXT DEFAULT '⭐',
        admin INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        daily TEXT DEFAULT ''
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner INTEGER,
        name TEXT,
        rarity TEXT,
        price INTEGER
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS market(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller INTEGER,
        nft_id INTEGER,
        price INTEGER
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS stats(
        user_id INTEGER PRIMARY KEY,
        games INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        jackpots INTEGER DEFAULT 0
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS achievements(
        user_id INTEGER,
        name TEXT,
        UNIQUE(user_id,name)
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS bans(
        user_id INTEGER PRIMARY KEY,
        reason TEXT DEFAULT ''
    )
    """)

init_db()

# ================= LANGUAGES =================

LANGUAGES = {
    "ru": {
        "welcome": "🎮 Добро пожаловать в MEGA BOT!",
        "games": "🎮 Игры",
        "profile": "👤 Профиль",
        "market": "💎 NFT Маркет",
        "settings": "⚙️ Настройки",
        "balance": "💰 Баланс",
        "bonus": "🎁 Ежедневный бонус",
        "back": "⬅️ Назад",
        "choose": "Выбери режим:"
    },
    "uk": {
        "welcome": "🎮 Ласкаво просимо!",
        "games": "🎮 Ігри",
        "profile": "👤 Профіль",
        "market": "💎 NFT Маркет",
        "settings": "⚙️ Налаштування",
        "balance": "💰 Баланс",
        "bonus": "🎁 Щоденний бонус",
        "back": "⬅️ Назад",
        "choose": "Обери режим:"
    },
    "en": {
        "welcome": "🎮 Welcome!",
        "games": "🎮 Games",
        "profile": "👤 Profile",
        "market": "💎 NFT Market",
        "settings": "⚙️ Settings",
        "balance": "💰 Balance",
        "bonus": "🎁 Daily bonus",
        "back": "⬅️ Back",
        "choose": "Choose a mode:"
    },
    "kk": {
        "welcome": "🎮 Қош келдің!",
        "games": "🎮 Ойындар",
        "profile": "👤 Профиль",
        "market": "💎 NFT Маркет",
        "settings": "⚙️ Баптаулар",
        "balance": "💰 Баланс",
        "bonus": "🎁 Күнделікті сыйлық",
        "back": "⬅️ Артқа",
        "choose": "Ойынды таңда:"
    }
}

def get_user(uid):
    return execute(
        "SELECT * FROM users WHERE id=?",
        (uid,)
    ).fetchone()

def register(message):
    uid = message.from_user.id
    username = message.from_user.username or "Без username"

    execute("""
    INSERT OR IGNORE INTO users(id,username)
    VALUES(?,?)
    """, (uid, username))

    execute(
        "UPDATE users SET username=? WHERE id=?",
        (username, uid)
    )

    return get_user(uid)

def lang(uid):
    user = get_user(uid)
    return user[5] if user else "ru"

def tr(uid, key):
    return LANGUAGES.get(
        lang(uid), LANGUAGES["ru"]
    ).get(key, key)

def banned(uid):
    user = get_user(uid)
    return not user or bool(user[8])

def add_balance(uid, amount):
    execute("""
    UPDATE users SET balance=balance+?
    WHERE id=?
    """, (amount, uid))

def add_xp(uid, amount):
    execute("""
    UPDATE users SET xp=xp+?
    WHERE id=?
    """, (amount, uid))

    user = get_user(uid)
    xp = user[3]
    level = xp // 500 + 1

    execute(
        "UPDATE users SET level=? WHERE id=?",
        (level, uid)
    )

def update_stats(uid, win=False, jackpot=False):
    execute("""
    INSERT OR IGNORE INTO stats(user_id)
    VALUES(?)
    """, (uid,))

    execute("""
    UPDATE stats
    SET games=games+1,
        wins=wins+?,
        jackpots=jackpots+?
    WHERE user_id=?
    """, (int(win), int(jackpot), uid))

# ================= KEYBOARDS =================

def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row("🎮 Игры", "👤 Профиль")
    kb.row("💎 NFT Маркет", "🎁 Бонус")
    kb.row("⚙️ Настройки", "🏆 Достижения")
    kb.row("📊 Топ игроков", "❓ Помощь")

    return kb

def game_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        ("🎰 Слоты", "slots"),
        ("🎲 Кубики", "dice"),
        ("🪙 Монетка", "coin"),
        ("🎯 Дартс", "dart"),
        ("🃏 Карты", "cards"),
        ("💣 Сапёр", "mines"),
        ("🧠 Викторина", "quiz"),
        ("🐉 Босс", "boss"),
        ("🎁 Кейсы", "cases")
    ]

    for title, callback in buttons:
        kb.add(
            types.InlineKeyboardButton(
                title,
                callback_data="game_" + callback
            )
        )

    return kb

# ================= NFT GENERATOR =================

PREFIXES = [
    "Golden", "Dark", "Cyber", "Mystic",
    "Royal", "Crystal", "Neon", "Shadow",
    "Ancient", "Legendary", "Frozen",
    "Electric", "Cosmic", "Lunar",
    "Solar", "Diamond", "Phantom"
]

OBJECTS = [
    "Dragon", "Tiger", "Crown", "Sword",
    "Cat", "Robot", "Ghost", "Phoenix",
    "Skull", "Wolf", "Gem", "Star",
    "Portal", "Mask", "Knight",
    "Treasure", "Planet", "Cactus",
    "Coconut", "Trophy"
]

RARITIES = [
    ("Обычный", 50, 100),
    ("Редкий", 20, 250),
    ("Эпический", 10, 600),
    ("Легендарный", 5, 1500),
    ("Мифический", 1, 5000)
]

def generate_nft(uid):
    name = random.choice(PREFIXES) + " " + random.choice(OBJECTS)
    rarity, minimum, maximum = random.choice(RARITIES)
    price = random.randint(minimum, maximum)

    execute("""
    INSERT INTO inventory(owner,name,rarity,price)
    VALUES(?,?,?,?)
    """, (uid, name, rarity, price))

    return name, rarity, price

# ================= ACHIEVEMENTS =================

ACHIEVEMENTS = {
    "first_game": "🎮 Первая игра",
    "first_win": "🏆 Первая победа",
    "jackpot": "🎰 Джекпот 777",
    "collector": "💎 Первый NFT",
    "rich": "💰 5000 монет",
    "boss": "🐉 Победитель босса"
}

def achievement(uid, name):
    if name not in ACHIEVEMENTS:
        return False

    try:
        execute("""
        INSERT INTO achievements(user_id,name)
        VALUES(?,?)
        """, (uid, name))
        return True
    except sqlite3.IntegrityError:
        return False

# ================= SLOTS =================

SLOT_SYMBOLS = [
    "🍒", "🍋", "🍇", "⭐", "💎", "7️⃣"
]

def slot_spin():
    result = [
        random.choice(SLOT_SYMBOLS)
        for _ in range(3)
    ]

    if result == ["7️⃣"] * 3:
        return result, 10, "🏆 ДЖЕКПОТ 777!"

    if len(set(result)) == 1:
        return result, 3, "🔥 ТРИ ОДИНАКОВЫХ!"

    if len(set(result)) == 2:
        return result, 1, "✨ ПАРА!"

    return result, 0, "😅 Не повезло!"

def play_slots(chat_id, uid):
    bet = 20

    user = get_user(uid)
    if user[2] < bet:
        bot.send_message(chat_id, "❌ Нужно 20 монет!")
        return

    add_balance(uid, -bet)

    msg = bot.send_message(
        chat_id,
        "🎰 | ❔ | ❔ | ❔\nКрутим барабаны..."
    )

    for frame in [
        "🎰 | 🍒 | ❔ | ❔",
        "🎰 | ⭐ | 🍋 | ❔",
        "🎰 | 💎 | 🍒 | ⭐",
        "🎰 | 🔄 | 🔄 | 🔄"
    ]:
        time.sleep(0.45)
        try:
            bot.edit_message_text(
                frame,
                chat_id,
                msg.message_id
            )
        except Exception:
            pass

    result, multiplier, title = slot_spin()
    reward = bet * multiplier

    if reward:
        add_balance(uid, reward)
        add_xp(uid, 20)

    update_stats(
        uid,
        reward > 0,
        multiplier == 10
    )

    if multiplier == 10:
        achievement(uid, "jackpot")

    bot.edit_message_text(
        f"🎰 {' | '.join(result)}\n\n"
        f"{title}\n"
        f"💰 Ставка: {bet}\n"
        f"🎁 Приз: {reward}",
        chat_id,
        msg.message_id
    )

# ================= DICE =================

def play_dice(chat_id, uid):
    user = get_user(uid)
    if user[2] < 10:
        bot.send_message(chat_id, "❌ Нужно 10 монет!")
        return

    add_balance(uid, -10)

    msg = bot.send_message(chat_id, "🎲 Бросаем кубик...")

    time.sleep(1)

    value = random.randint(1, 6)
    reward = 30 if value >= 5 else 0

    if reward:
        add_balance(uid, reward)
        add_xp(uid, 10)

    update_stats(uid, reward > 0)

    bot.edit_message_text(
        f"🎲 Выпало: {value}\n"
        f"🎁 Награда: {reward}",
        chat_id,
        msg.message_id
    )

# ================= COIN =================

def play_coin(chat_id, uid):
    user = get_user(uid)

    if user[2] < 10:
        bot.send_message(chat_id, "❌ Нужно 10 монет!")
        return

    add_balance(uid, -10)

    result = random.choice(["Орёл 🦅", "Решка 🪙"])

    bot.send_message(
        chat_id,
        "🪙 Монетка подбрасывается...\n\n" + result
    )

    reward = 20 if result.startswith("Орёл") else 0

    if reward:
        add_balance(uid, reward)

    update_stats(uid, reward > 0)

# ================= DART =================

def play_dart(chat_id, uid):
    user = get_user(uid)

    if user[2] < 10:
        bot.send_message(chat_id, "❌ Нужно 10 монет!")
        return

    add_balance(uid, -10)

    msg = bot.send_dice(chat_id, emoji="🎯")
    time.sleep(1)

    points = msg.dice.value
    reward = points * 10

    add_balance(uid, reward)
    add_xp(uid, 10)
    update_stats(uid, reward > 0)

    bot.send_message(
        chat_id,
        f"🎯 Очки: {points}\n💰 Получено: {reward}"
    )

# ================= HIGH LOW =================

def play_cards(chat_id, uid):
    cards = [
        ("2", 2), ("3", 3), ("4", 4),
        ("5", 5), ("6", 6), ("7", 7),
        ("8", 8), ("9", 9), ("10", 10),
        ("J", 11), ("Q", 12),
        ("K", 13), ("A", 14)
    ]

    first, second = random.sample(cards, 2)

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "⬆️ Выше",
            callback_data=f"card_higher_{first[1]}_{second[1]}"
        ),
        types.InlineKeyboardButton(
            "⬇️ Ниже",
            callback_data=f"card_lower_{first[1]}_{second[1]}"
        )
    )

    bot.send_message(
        chat_id,
        f"🃏 Первая карта: {first[0]}\n"
        "Вторая карта будет выше или ниже?",
        reply_markup=kb
    )

# ================= MINES =================

def mines_game(chat_id, uid):
    kb = types.InlineKeyboardMarkup(row_width=3)

    for i in range(9):
        kb.insert(
            types.InlineKeyboardButton(
                "❔",
                callback_data=f"mine_{i}"
            )
        )

    bot.send_message(
        chat_id,
        "💣 Сапёр! Найди безопасную клетку.",
        reply_markup=kb
    )

# ================= QUIZ =================

def quiz_game(chat_id):
    questions = [
        ("Сколько будет 5×5?", ["20", "25", "30"], 1),
        ("Столица Франции?", ["Париж", "Рим", "Берлин"], 0),
        ("Сколько планет в Солнечной системе?", ["7", "8", "9"], 1),
        ("Какой океан самый большой?", ["Тихий", "Атлантический", "Индийский"], 0),
        ("Сколько минут в часе?", ["50", "60", "100"], 1)
    ]

    q = random.choice(questions)

    kb = types.InlineKeyboardMarkup()

    for i, answer in enumerate(q[1]):
        kb.add(
            types.InlineKeyboardButton(
                answer,
                callback_data=f"quiz_{i}_{q[2]}"
            )
        )

    bot.send_message(
        chat_id,
        "🧠 " + q[0],
        reply_markup=kb
    )

# ================= BOSS =================

def boss_game(chat_id, uid):
    result = random.randint(1, 100)

    if result > 40:
        reward = 100
        add_balance(uid, reward)
        add_xp(uid, 50)
        achievement(uid, "boss")

        bot.send_message(
            chat_id,
            "🐉 БОСС ПОБЕЖДЁН!\n"
            f"🏆 Награда: {reward} монет!"
        )
    else:
        bot.send_message(
            chat_id,
            "🐉 Босс оказался сильнее!\n"
            "Попробуй ещё раз."
        )

    update_stats(uid, result > 40)

# ================= CASES =================

CASE_TYPES = {
    "common": (100, 50, 180),
    "rare": (250, 150, 500),
    "epic": (500, 300, 1200),
    "legendary": (1000, 500, 3000)
}

def cases_menu(chat_id):
    kb = types.InlineKeyboardMarkup()

    for name, cost in [
        ("Обычный", "common"),
        ("Редкий", "rare"),
        ("Эпический", "epic"),
        ("Легендарный", "legendary")
    ]:
        kb.add(
            types.InlineKeyboardButton(
                name,
                callback_data="case_" + cost
            )
        )

    bot.send_message(
        chat_id,
        "🎁 Выбери виртуальный кейс:",
        reply_markup=kb
    )

def open_case(uid, chat_id, case):
    if case not in CASE_TYPES:
        return

    cost, minimum, maximum = CASE_TYPES[case]
    user = get_user(uid)

    if user[2] < cost:
        bot.send_message(chat_id, "❌ Не хватает монет!")
        return

    add_balance(uid, -cost)

    reward = random.randint(minimum, maximum)
    add_balance(uid, reward)

    name, rarity, price = generate_nft(uid)
    achievement(uid, "collector")

    bot.send_message(
        chat_id,
        "🎁 КЕЙС ОТКРЫТ!\n\n"
        f"💰 Монеты: +{reward}\n"
        f"💎 NFT: {name}\n"
        f"⭐ Редкость: {rarity}"
    )

# ================= DAILY =================

def daily(uid, chat_id):
    user = get_user(uid)
    today = time.strftime("%Y-%m-%d")

    if user[9] == today:
        bot.send_message(chat_id, "⏳ Бонус уже получен!")
        return

    reward = random.randint(100, 300)

    execute(
        "UPDATE users SET balance=balance+?,daily=? WHERE id=?",
        (reward, today, uid)
    )

    bot.send_message(
        chat_id,
        f"🎁 Ежедневная награда: +{reward} монет!"
    )

# ================= PROFILE =================

def profile(uid, chat_id):
    user = get_user(uid)

    stats = execute(
        "SELECT games,wins,jackpots FROM stats WHERE user_id=?",
        (uid,)
    ).fetchone()

    games, wins, jackpots = stats or (0, 0, 0)

    nft_count = execute(
        "SELECT COUNT(*) FROM inventory WHERE owner=?",
        (uid,)
    ).fetchone()[0]

    bot.send_message(
        chat_id,
        f"👤 ПРОФИЛЬ\n\n"
        f"🆔 ID: {uid}\n"
        f"⭐ Уровень: {user[4]}\n"
        f"✨ XP: {user[3]}\n"
        f"💰 Баланс: {user[2]}\n"
        f"💎 NFT: {nft_count}\n"
        f"🎮 Игр: {games}\n"
        f"🏆 Побед: {wins}\n"
        f"🎰 Джекпотов: {jackpots}"
    )

# ================= INVENTORY =================

def inventory(uid, chat_id):
    items = execute(
        "SELECT id,name,rarity,price FROM inventory WHERE owner=?",
        (uid,)
    ).fetchall()

    if not items:
        bot.send_message(chat_id, "💎 Коллекция пока пуста!")
        return

    text = "💎 ТВОИ NFT:\n\n"

    for item in items:
        text += (
            f"#{item[0]} — {item[1]}\n"
            f"⭐ {item[2]} | 💰 {item[3]}\n\n"
        )

    bot.send_message(chat_id, text)

# ================= MARKET =================

def market_menu(chat_id):
    items = execute("""
    SELECT market.id, inventory.name,
           inventory.rarity, market.price
    FROM market
    JOIN inventory ON inventory.id=market.nft_id
    LIMIT 15
    """).fetchall()

    if not items:
        bot.send_message(chat_id, "💎 Маркет пока пуст!")
        return

    for item in items:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                "🛒 Купить",
                callback_data=f"buy_{item[0]}"
            )
        )

        bot.send_message(
            chat_id,
            f"💎 {item[1]}\n"
            f"⭐ {item[2]}\n"
            f"💰 Цена: {item[3]}",
            reply_markup=kb
        )

# ================= SETTINGS =================

def settings(chat_id):
    kb = types.InlineKeyboardMarkup()

    for code, name in [
        ("ru", "🇷🇺 Русский"),
        ("uk", "🇺🇦 Українська"),
        ("en", "🇬🇧 English"),
        ("kk", "🇰🇿 Қазақша")
    ]:
        kb.add(
            types.InlineKeyboardButton(
                name,
                callback_data="language_" + code
            )
        )

    bot.send_message(
        chat_id,
        "⚙️ Выбери язык:",
        reply_markup=kb
    )

# ================= LEADERBOARD =================

def leaderboard(chat_id):
    users = execute("""
    SELECT id,username,balance,level
    FROM users
    WHERE banned=0
    ORDER BY balance DESC
    LIMIT 10
    """).fetchall()

    text = "🏆 ТОП ИГРОКОВ\n\n"

    for i, user in enumerate(users, 1):
        text += (
            f"{i}. {user[1]} — "
            f"💰 {user[2]} | ⭐ {user[3]}\n"
        )

    bot.send_message(chat_id, text)

# ================= ADMIN =================

def admin_menu(chat_id):
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "📊 Статистика",
            callback_data="admin_stats"
        )
    )

    bot.send_message(
        chat_id,
        "🛠️ ADMIN PANEL",
        reply_markup=kb
    )

# ================= START =================

@bot.message_handler(commands=["start"])
def start(message):
    register(message)
    uid = message.from_user.id

    if banned(uid):
        return

    bot.send_message(
        message.chat.id,
        tr(uid, "welcome"),
        reply_markup=main_menu(uid)
    )

# ================= ADMIN LOGIN =================

@bot.message_handler(commands=["admin"])
def admin_login(message):
    uid = message.from_user.id

    if not get_user(uid):
        register(message)

    msg = bot.send_message(
        message.chat.id,
        "🔐 Введи секретный код:"
    )

    bot.register_next_step_handler(
        msg,
        check_admin_code
    )

def check_admin_code(message):
    uid = message.from_user.id

    if message.text != ADMIN_CODE:
        bot.send_message(message.chat.id, "❌ Неверный код!")
        return

    execute(
        "UPDATE users SET admin=1 WHERE id=?",
        (uid,)
    )

    bot.send_message(
        message.chat.id,
        "🛠️ Доступ администратора открыт!"
    )

    admin_menu(message.chat.id)

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text"])
def messages(message):
    uid = message.from_user.id
    chat = message.chat.id
    text = message.text

    register(message)

    if banned(uid):
        return

    if text == "🎮 Игры":
        bot.send_message(
            chat,
            tr(uid, "choose"),
            reply_markup=game_menu()
        )

    elif text == "👤 Профиль":
        profile(uid, chat)

    elif text == "💎 NFT Маркет":
        market_menu(chat)

    elif text == "🎁 Бонус":
        daily(uid, chat)

    elif text == "⚙️ Настройки":
        settings(chat)

    elif text == "🏆 Достижения 

    TELEGRAM_TOKEN=9133073082:AAEMW6Uv6S2wvcEII7xlXmUNp4KdHsRqpRE
ADMIN_CODE=2849
    
