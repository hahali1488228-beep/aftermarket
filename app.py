
import os
import json
import time
import random
import sqlite3
import threading
import urllib.request
import urllib.parse
from flask import Flask

# ==================================================
# NFT GAME BOT V2
# ==================================================

TOKEN = os.environ["TELEGRAM_TOKEN"]
ADMIN_CODE = os.environ.get("ADMIN_CODE", "76161")
API = f"https://api.telegram.org/bot{TOKEN}/"

CHANNEL = "https://t.me/marketnft111"
SUPPORT = "https://t.me/LYCIK002"

DB = "game.db"
app = Flask(__name__)

# ==================================================
# DATABASE
# ==================================================

db = sqlite3.connect(DB, check_same_thread=False)
db.row_factory = sqlite3.Row
lock = threading.RLock()

def init_db():
    with lock:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 500,
            lang TEXT DEFAULT 'ru',
            decoration TEXT DEFAULT '⭐',
            is_admin INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS inventory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner INTEGER,
            name TEXT,
            rarity TEXT,
            emoji TEXT,
            price INTEGER
        );

        CREATE TABLE IF NOT EXISTS listings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nft_id INTEGER,
            seller INTEGER,
            price INTEGER
        );

        CREATE TABLE IF NOT EXISTS stats(
            user_id INTEGER PRIMARY KEY,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            games INTEGER DEFAULT 0
        );
        """)
        db.commit()

init_db()

def query(sql, args=()):
    with lock:
        cur = db.execute(sql, args)
        db.commit()
        return cur

def get_user(uid, username=""):
    uid = int(uid)
    u = query("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u:
        query(
            "INSERT INTO users(id,username) VALUES(?,?)",
            (uid, username or "unknown")
        )
        query("INSERT INTO stats(user_id) VALUES(?)", (uid,))
        u = query("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    elif username:
        query("UPDATE users SET username=? WHERE id=?", (username, uid))
        u = query("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return u

def coins(uid):
    return get_user(uid)["coins"]

def add_coins(uid, amount):
    query("UPDATE users SET coins=coins+? WHERE id=?", (int(amount), int(uid)))

def take_coins(uid, amount):
    u = get_user(uid)
    if u["coins"] < amount:
        return False
    query("UPDATE users SET coins=coins-? WHERE id=?", (amount, int(uid)))
    return True

def stats(uid, win):
    query("""
    UPDATE stats SET games=games+1,
    wins=wins+?, losses=losses+?
    WHERE user_id=?
    """, (int(win), int(not win), int(uid)))

# ==================================================
# NFT CATALOG — 300+ COMBINATIONS
# ==================================================

PREFIXES = [
    "Космический", "Золотой", "Тёмный", "Неоновый",
    "Ледяной", "Огненный", "Королевский", "Древний",
    "Мистический", "Кибер", "Легендарный", "Секретный",
    "Радужный", "Призрачный", "Эпический", "Драконий",
    "Кристальный", "Галактический", "Пиксельный", "Магический"
]

OBJECTS = [
    ("Кот", "🐱"), ("Пёс", "🐶"), ("Дракон", "🐉"),
    ("Алмаз", "💎"), ("Корона", "👑"), ("Ракета", "🚀"),
    ("Призрак", "👻"), ("Робот", "🤖"), ("Планета", "🪐"),
    ("Меч", "⚔️"), ("Щит", "🛡️"), ("Звезда", "⭐"),
    ("Кристалл", "🔮"), ("Пицца", "🍕"), ("Коробка", "🎁"),
    ("Череп", "💀"), ("Лиса", "🦊"), ("Единорог", "🦄"),
    ("Тигр", "🐯"), ("Пингвин", "🐧")
]

RARITIES = [
    ("Обычный", 50, 100),
    ("Редкий", 100, 250),
    ("Эпический", 250, 600),
    ("Легендарный", 600, 1500),
    ("Мифический", 1500, 5000)
]

def generate_nft():
    prefix = random.choice(PREFIXES)
    name, emoji = random.choice(OBJECTS)
    rarity, low, high = random.choice(RARITIES)
    return {
        "name": f"{prefix} {name}",
        "emoji": emoji,
        "rarity": rarity,
        "price": random.randint(low, high)
    }

def create_nft(uid):
    nft = generate_nft()
    query("""
    INSERT INTO inventory(owner,name,rarity,emoji,price)
    VALUES(?,?,?,?,?)
    """, (uid, nft["name"], nft["rarity"],
          nft["emoji"], nft["price"]))
    return nft

# ==================================================
# TRANSLATIONS
# ==================================================

LANGS = {
    "ru": {
        "welcome": "👋 Добро пожаловать в NFT GAME!",
        "balance": "Баланс",
        "games": "🎮 Игры",
        "casino": "🎰 Игровой зал",
        "profile": "👤 Профиль",
        "settings": "⚙️ Настройки",
        "market": "🛒 NFT Маркет",
        "inventory": "💎 Инвентарь",
        "channel": "📢 Канал",
        "support": "❤️ Поддержать автора",
        "back": "⬅️ Назад",
        "choose": "Выбери действие:",
        "bet": "Введи ставку от 1 до 10000:",
        "no_money": "❌ Недостаточно монет!",
        "win": "🎉 Победа!",
        "lose": "😢 Проигрыш!",
        "language": "Выбери язык:",
        "admin": "👑 Админ-панель",
        "id": "Твой ID",
        "guess": "🔢 Угадай число",
        "coin": "🪙 Монетка",
        "dice": "🎲 Кубик",
        "slots": "🎰 Слоты",
        "roulette": "🔴 Рулетка",
        "decor": "🎨 Украшение профиля",
        "sell": "💰 Продать NFT",
        "buy": "🛒 Купить NFT"
    },
    "uk": {
        "welcome": "👋 Ласкаво просимо до NFT GAME!",
        "balance": "Баланс",
        "games": "🎮 Ігри",
        "casino": "🎰 Ігрова зала",
        "profile": "👤 Профіль",
        "settings": "⚙️ Налаштування",
        "market": "🛒 NFT Маркет",
        "inventory": "💎 Інвентар",
        "channel": "📢 Канал",
        "support": "❤️ Підтримати автора",
        "back": "⬅️ Назад",
        "choose": "Обери дію:",
        "bet": "Введи ставку від 1 до 10000:",
        "no_money": "❌ Недостатньо монет!",
        "win": "🎉 Перемога!",
        "lose": "😢 Поразка!",
        "language": "Обери мову:",
        "admin": "👑 Адмін-панель",
        "id": "Твій ID",
        "guess": "🔢 Вгадай число",
        "coin": "🪙 Монетка",
        "dice": "🎲 Кубик",
        "slots": "🎰 Слоти",
        "roulette": "🔴 Рулетка",
        "decor": "🎨 Прикраса профілю",
        "sell": "💰 Продати NFT",
        "buy": "🛒 Купити NFT"
    },
    "en": {
        "welcome": "👋 Welcome to NFT GAME!",
        "balance": "Balance",
        "games": "🎮 Games",
        "casino": "🎰 Game room",
        "profile": "👤 Profile",
        "settings": "⚙️ Settings",
        "market": "🛒 NFT Market",
        "inventory": "💎 Inventory",
        "channel": "📢 Channel",
        "support": "❤️ Support author",
        "back": "⬅️ Back",
        "choose": "Choose an action:",
        "bet": "Enter a stake from 1 to 10000:",
        "no_money": "❌ Not enough coins!",
        "win": "🎉 You won!",
        "lose": "😢 You lost!",
        "language": "Choose language:",
        "admin": "👑 Admin panel",
        "id": "Your ID",
        "guess": "🔢 Guess the number",
        "coin": "🪙 Coin",
        "dice": "🎲 Dice",
        "slots": "🎰 Slots",
        "roulette": "🔴 Roulette",
        "decor": "🎨 Profile decoration",
        "sell": "💰 Sell NFT",
        "buy": "🛒 Buy NFT"
    },
    "kz": {
        "welcome": "👋 NFT GAME-ге қош келдің!",
        "balance": "Баланс",
        "games": "🎮 Ойындар",
        "casino": "🎰 Ойын бөлмесі",
        "profile": "👤 Профиль",
        "settings": "⚙️ Баптаулар",
        "market": "🛒 NFT базары",
        "inventory": "💎 Инвентарь",
        "channel": "📢 Арна",
        "support": "❤️ Авторды қолдау",
        "back": "⬅️ Артқа",
        "choose": "Әрекетті таңда:",
        "bet": "1-ден 10000-ға дейінгі ставканы енгіз:",
        "no_money": "❌ Монета жеткіліксіз!",
        "win": "🎉 Жеңіс!",
        "lose": "😢 Жеңіліс!",
        "language": "Тілді таңда:",
        "admin": "👑 Әкімші панелі",
        "id": "Сенің ID",
        "guess": "🔢 Сан тап",
        "coin": "🪙 Тиын",
        "dice": "🎲 Текше",
        "slots": "🎰 Слоттар",
        "roulette": "🔴 Рулетка",
        "decor": "🎨 Профиль безендіру",
        "sell": "💰 NFT сату",
        "buy": "🛒 NFT сатып алу"
    }
}

def T(uid, key):
    lang = get_user(uid)["lang"]
    return LANGS.get(lang, LANGS["ru"]).get(key, key)

# ==================================================
# TELEGRAM API
# ==================================================

def api(method, params=None):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(API + method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("API ERROR:", e)
        return {}

def send(cid, text, keyboard=None):
    p = {"chat_id": cid, "text": text}
    if keyboard:
        p["reply_markup"] = json.dumps(keyboard, ensure_ascii=False)
    return api("sendMessage", p)

def edit(cid, mid, text, keyboard=None):
    p = {"chat_id": cid, "message_id": mid, "text": text}
    if keyboard:
        p["reply_markup"] = json.dumps(keyboard, ensure_ascii=False)
    return api("editMessageText", p)

def answer(cid, text=""):
    api("answerCallbackQuery", {
        "callback_query_id": cid,
        "text": text
    })

def buttons(rows):
    return {"inline_keyboard": rows}

# ==================================================
# MENUS
# ==================================================

def home(uid):
    return buttons([
        [{"text": T(uid, "games"), "callback_data": "games"},
         {"text": T(uid, "profile"), "callback_data": "profile"}],
        [{"text": T(uid, "market"), "callback_data": "market"},
         {"text": T(uid, "inventory"), "callback_data": "inventory"}],
        [{"text": T(uid, "settings"), "callback_data": "settings"}],
        [{"text": T(uid, "support"), "url": SUPPORT}],
        [{"text": T(uid, "channel"), "url": CHANNEL}]
    ])

def games_menu(uid):
    names = [
        ("guess", "guess"),
        ("coin", "coin"),
        ("dice", "dice"),
        ("slots", "slots"),
        ("roulette", "roulette")
    ]
    rows = [[{"text": T(uid, label), "callback_data": "game_" + code}]
            for label, code in names]
    rows.append([{"text": T(uid, "back"), "callback_data": "home"}])
    return buttons(rows)

def settings_menu(uid):
    rows = [
        [{"text": "🌍 Язык / Language", "callback_data": "languages"}],
        [{"text": T(uid, "decor"), "callback_data": "decor"}],
        [{"text": "👑 Админка", "callback_data": "admin_login"}],
        [{"text": T(uid, "back"), "callback_data": "home"}]
    ]
    return buttons(rows)

def language_menu():
    return buttons([
        [{"text": "🇺🇦 Українська", "callback_data": "lang_uk"}],
        [{"text": "🇷🇺 Русский", "callback_data": "lang_ru"}],
        [{"text": "🇬🇧 English", "callback_data": "lang_en"}],
        [{"text": "🇰🇿 Қазақша", "callback_data": "lang_kz"}],
        [{"text": "⬅️", "callback_data": "settings"}]
    ])

def profile(uid):
    u = get_user(uid)
    s = query("SELECT * FROM stats WHERE user_id=?", (uid,)).fetchone()
    nft_count = query(
        "SELECT COUNT(*) n FROM inventory WHERE owner=?", (uid,)
    ).fetchone()["n"]
    badge = " ☑️" if u["is_admin"] else ""
    return (
        f"{u['decoration']} ПРОФИЛЬ{badge}\n\n"
        f"👤 @{u['username']}\n"
        f"🆔 ID: {uid}\n"
        f"🪙 {T(uid,'balance')}: {u['coins']}\n"
        f"💎 NFT: {nft_count}\n"
        f"🏆 Побед: {s['wins']}\n"
        f"😢 Поражений: {s['losses']}\n"
        f"🎮 Игр: {s['games']}"
    )

# ==================================================
# GAME SYSTEM
# ==================================================

states = {}

GAME_NAMES = {
    "guess": "Угадай число",
    "coin": "Монетка",
    "dice": "Кубик",
    "slots": "Слоты",
    "roulette": "Рулетка"
}

def game_start(uid, game, cid):
    states[uid] = {"step": "bet", "game": game}
    send(cid, T(uid, "bet"))

def play_game(uid, cid, bet):
    state = states.get(uid)
    if not state:
        return

    game = state["game"]
    if bet < 1 or bet > 10000:
        send(cid, "Ставка должна быть от 1 до 10000.")
        return

    if not take_coins(uid, bet):
        send(cid, T(uid, "no_money"))
        return

    # Guessing game: player must actually choose a number.
    if game == "guess":
        state.update({
            "step": "guess",
            "bet": bet,
            "number": random.randint(1, 5)
        })
        send(cid, "🔢 Угадай число от 1 до 5:",
             buttons([[{"text": str(n), "callback_data": f"guess_{n}"}
                       for n in range(1, 6)],
                      [{"text": "Отмена", "callback_data": "cancel"}]]))
        return

    win = False
    reward = 0
    result = ""

    if game == "coin":
        result = random.choice(["Орёл", "Решка"])
        win = result == "Орёл"
        reward = bet * 2 if win else 0

    elif game == "dice":
        roll = random.randint(1, 6)
        result = f"🎲 Выпало: {roll}"
        win = roll >= 5
        reward = bet * 2 if win else 0

    elif game == "slots":
        symbols = ["🍒", "🍋", "🍇", "💎", "⭐"]
        result = [random.choice(symbols) for _ in range(3)]
        if len(set(result)) == 1:
            win, reward = True, bet * 5
        elif len(set(result)) == 2:
            win, reward = True, bet * 2
        result = " | ".join(result)

    elif game == "roulette":
        number = random.randint(0, 36)
        result = f"🔴 Выпало число: {number}"
        win = number % 2 == 0 and number != 0
        reward = bet * 2 if win else 0

    if win:
        add_coins(uid, reward)
        stats(uid, True)
        msg = f"{T(uid,'win')}\n{result}\n+{reward} 🪙"
    else:
        stats(uid, False)
        msg = f"{T(uid,'lose')}\n{result}\n-{bet} 🪙"

    states.pop(uid, None)
    send(cid, msg, games_menu(uid))

def guess_answer(uid, cid, number):
    state = states.get(uid)
    if not state or state.get("step") != "guess":
        return

    bet = state["bet"]
    correct = state["number"]
    if number == correct:
        reward = bet * 5
        add_coins(uid, reward)
        stats(uid, True)
        msg = f"🎉 Правильно! Загаданное число: {correct}\n+{reward} 🪙"
    else:
        stats(uid, False)
        msg = f"😢 Не угадал! Было число {correct}.\n-{bet} 🪙"

    states.pop(uid, None)
    send(cid, msg, games_menu(uid))

# ==================================================
# NFT MARKET
# ==================================================

def inventory_menu(uid):
    items = query(
        "SELECT * FROM inventory WHERE owner=? ORDER BY id DESC LIMIT 10",
        (uid,)
    ).fetchall()

    rows = []
    text = "💎 ТВОЙ ИНВЕНТАРЬ\n\n"

    if not items:
        text += "Пока пусто. Купи NFT в магазине!"
    else:
        for n in items:
            text += (
                f"\n{n['emoji']} {n['name']}\n"
                f"Редкость: {n['rarity']}\n"
                f"Цена: {n['price']} 🪙\n"
            )
            rows.append([{
                "text": f"💰 Продать #{n['id']}",
                "callback_data": f"sell_{n['id']}"
            }])

    rows.append([{"text": "⬅️ Назад", "callback_data": "home"}])
    return text, buttons(rows)

def market_menu(uid):
    items = query("""
    SELECT listings.id, listings.price, inventory.name,
    inventory.emoji, inventory.rarity, inventory.id AS nft_id,
    listings.seller
    FROM listings JOIN inventory ON listings.nft_id=inventory.id
    ORDER BY listings.id DESC LIMIT 15
    """).fetchall()

    text = "🛒 NFT MARKET\n\n"
    rows = []

    if not items:
        text += "Пока никто ничего не продаёт."
    else:
        for n in items:
            seller = get_user(n["seller"])
            text += (
                f"{n['emoji']} {n['name']}\n"
                f"Редкость: {n['rarity']}\n"
                f"Цена: {n['price']} 🪙\n"
                f"Продавец: @{seller['username']}\n\n"
            )
            rows.append([{
                "text": f"Купить #{n['id']} за {n['price']} 🪙",
                "callback_data": f"buy_{n['id']}"
            }])

    rows.append([{"text": "⬅️ Назад", "callback_data": "home"}])
    return text, buttons(rows)

def sell_nft(uid, nft_id, cid):
    nft = query(
        "SELECT * FROM inventory WHERE id=? AND owner=?",
        (nft_id, uid)
    ).fetchone()

    if not nft:
        send(cid, "NFT не найден.")
        return

    states[uid] = {"step": "sell_price", "nft_id": nft_id}
    send(cid, f"Введи цену продажи NFT {nft['name']}:")

def buy_nft(uid, listing_id, cid):
    item = query(
        "SELECT * FROM listings WHERE id=?", (listing_id,)
    ).fetchone()

    if not item:
        send(cid, "Лот уже недоступен.")
        return

    if item["seller"] == uid:
        send(cid, "Нельзя купить собственный NFT.")
        return

    if coins(uid) < item["price"]:
        send(cid, "Недостаточно монет.")
        return

    with lock:
        db.execute("BEGIN IMMEDIATE")
        try:
            listing = db.execute(
                "SELECT * FROM listings WHERE id=?", (listing_id,)
            ).fetchone()

            if not listing:
                db.rollback()
                send(cid, "Лот уже купили.")
                return

            nft = db.execute(
                "SELECT * FROM inventory WHERE id=? AND owner=?",
                (listing["nft_id"], listing["seller"])
            ).fetchone()

            if not nft:
                db.execute("DELETE FROM listings WHERE id=?", (listing_id,))
                db.commit()
                send(cid, "Лот больше недоступен.")
                return

            buyer = db.execute(
                "SELECT coins FROM users WHERE id=?", (uid,)
            ).fetchone()

            if not buyer or buyer["coins"] < listing["price"]:
                db.rollback()
                send(cid, "Недостаточно монет.")
                return

            db.execute(
                "UPDATE users SET coins=coins-? WHERE id=?",
                (listing["price"], uid)
            )
            db.execute(
                "UPDATE users SET coins=coins+? WHERE id=?",
                (listing["price"], listing["seller"])
            )
            db.execute(
                "UPDATE inventory SET owner=? WHERE id=?",
                (uid, listing["nft_id"])
            )
            db.execute("DELETE FROM listings WHERE id=?", (listing_id,))
            db.commit()
        except Exception:
            db.rollback()
            raise

    send(cid, f"🎉 Ты купил {nft['name']}!")

# ==================================================
# ADMIN PANEL
# ==================================================

def admin_menu():
    return buttons([
        [{"text": "➕ Начислить монеты", "callback_data": "admin_add"}],
        [{"text": "🚫 Забанить ID", "callback_data": "admin_ban"}],
        [{"text": "✅ Разбанить ID", "callback_data": "admin_unban"}],
        [{"text": "👑 Выдать администратора", "callback_data": "admin_give"}],
        [{"text": "📊 Статистика бота", "callback_data": "admin_stats"}],
        [{"text": "🎁 Выдать NFT", "callback_data": "admin_nft"}],
        [{"text": "⬅️ Назад", "callback_data": "settings"}]
    ])

def admin_action(uid, action, cid):
    states[uid] = {"step": action}
    prompts = {
        "admin_add": "Введи ID пользователя и количество монет через пробел:",
        "admin_ban": "Введи ID пользователя для бана:",
        "admin_unban": "Введи ID пользователя для разбана:",
        "admin_give": "Введи ID пользователя:",
        "admin_nft": "Введи ID пользователя для выдачи NFT:"
    }
    send(cid, prompts[action])

# ================
