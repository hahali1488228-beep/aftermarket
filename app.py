
import os
import json
import time
import random
import threading
import urllib.request
import urllib.parse
from flask import Flask

# =========================
# CONFIG
# =========================

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_CODE = os.environ.get("ADMIN_CODE", "76161")

if not TOKEN:
    raise RuntimeError("Добавь TELEGRAM_TOKEN в Environment!")

API_URL = f"https://api.telegram.org/bot{TOKEN}/"

DB_USERS = "users.json"
DB_SETTINGS = "settings.json"

CHANNEL = "https://t.me/marketnft111"
AUTHOR = "https://t.me/LYCIK002"

LANGUAGES = {
    "ru": {
        "welcome": "👋 Добро пожаловать!\n\n💰 Баланс: {balance} 🪙",
        "support": "❤️ Поддержать авторов",
        "games": "🎮 Игры",
        "casino": "🎰 Казино",
        "settings": "⚙️ Настройки",
        "channel": "📢 Канал",
        "profile": "👤 Профиль",
        "back": "⬅️ Назад",
        "choose_game": "🎮 Выбери игру:",
        "choose_bet": "🪙 Выбери ставку:",
        "balance": "💰 Баланс",
        "language": "🌍 Выбери язык:",
        "saved": "✅ Язык изменён!",
        "admin": "👑 Админка",
        "enter_code": "🔐 Введи секретный код:",
        "wrong_code": "❌ Неверный код!",
        "admin_ok": "👑 Админка открыта!",
        "stats": "👥 Пользователей: {users}\n🪙 Всего монет: {coins}",
        "no_money": "❌ Недостаточно монет!",
        "win": "🎉 Победа! Ты получил {amount} монет!",
        "lose": "😢 Проигрыш! Ты потерял {amount} монет.",
        "profile_text": "👤 Твой профиль\n\n🆔 ID: {id}\n🪙 Баланс: {balance}\n🎮 Игр сыграно: {games}",
        "roulette": "🔴 Рулетка",
        "slots": "🎰 Слоты",
        "dice": "🎲 Кубик",
        "coin": "🪙 Монетка",
        "number": "🔢 Угадай число",
        "casino_info": "🎰 Игровое казино\n\nИспользуются только виртуальные монеты.",
        "admin_panel": "👑 Панель администратора",
        "cancel": "❌ Отмена"
    },

    "uk": {
        "welcome": "👋 Ласкаво просимо!\n\n💰 Баланс: {balance} 🪙",
        "support": "❤️ Підтримати авторів",
        "games": "🎮 Ігри",
        "casino": "🎰 Казино",
        "settings": "⚙️ Налаштування",
        "channel": "📢 Канал",
        "profile": "👤 Профіль",
        "back": "⬅️ Назад",
        "choose_game": "🎮 Обери гру:",
        "choose_bet": "🪙 Обери ставку:",
        "balance": "💰 Баланс",
        "language": "🌍 Обери мову:",
        "saved": "✅ Мову змінено!",
        "admin": "👑 Адмінка",
        "enter_code": "🔐 Введи секретний код:",
        "wrong_code": "❌ Неправильний код!",
        "admin_ok": "👑 Адмінку відкрито!",
        "stats": "👥 Користувачів: {users}\n🪙 Усього монет: {coins}",
        "no_money": "❌ Недостатньо монет!",
        "win": "🎉 Перемога! Ти отримав {amount} монет!",
        "lose": "😢 Поразка! Ти втратив {amount} монет.",
        "profile_text": "👤 Твій профіль\n\n🆔 ID: {id}\n🪙 Баланс: {balance}\n🎮 Ігор зіграно: {games}",
        "roulette": "🔴 Рулетка",
        "slots": "🎰 Слоти",
        "dice": "🎲 Кубик",
        "coin": "🪙 Монетка",
        "number": "🔢 Вгадай число",
        "casino_info": "🎰 Ігрове казино\n\nВикористовуються лише віртуальні монети.",
        "admin_panel": "👑 Панель адміністратора",
        "cancel": "❌ Скасувати"
    },

    "kk": {
        "welcome": "👋 Қош келдің!\n\n💰 Баланс: {balance} 🪙",
        "support": "❤️ Авторларды қолдау",
        "games": "🎮 Ойындар",
        "casino": "🎰 Казино",
        "settings": "⚙️ Баптаулар",
        "channel": "📢 Арна",
        "profile": "👤 Профиль",
        "back": "⬅️ Артқа",
        "choose_game": "🎮 Ойынды таңда:",
        "choose_bet": "🪙 Тігімді таңда:",
        "balance": "💰 Баланс",
        "language": "🌍 Тілді таңда:",
        "saved": "✅ Тіл өзгертілді!",
        "admin": "👑 Әкімші",
        "enter_code": "🔐 Құпия кодты енгіз:",
        "wrong_code": "❌ Қате код!",
        "admin_ok": "👑 Әкімші бөлімі ашылды!",
        "stats": "👥 Қолданушылар: {users}\n🪙 Барлық тиындар: {coins}",
        "no_money": "❌ Тиын жеткіліксіз!",
        "win": "🎉 Жеңіс! Сен {amount} тиын алдың!",
        "lose": "😢 Жеңіліс! Сен {amount} тиын жоғалттың.",
        "profile_text": "👤 Профиль\n\n🆔 ID: {id}\n🪙 Баланс: {balance}\n🎮 Ойындар: {games}",
        "roulette": "🔴 Рулетка",
        "slots": "🎰 Слоттар",
        "dice": "🎲 Кубик",
        "coin": "🪙 Тиын",
        "number": "🔢 Сан тап",
        "casino_info": "🎰 Ойын казиносы\n\nТек виртуалды тиындар қолданылады.",
        "admin_panel": "👑 Әкімші панелі",
        "cancel": "❌ Болдырмау"
    },

    "en": {
        "welcome": "👋 Welcome!\n\n💰 Balance: {balance} 🪙",
        "support": "❤️ Support authors",
        "games": "🎮 Games",
        "casino": "🎰 Casino",
        "settings": "⚙️ Settings",
        "channel": "📢 Channel",
        "profile": "👤 Profile",
        "back": "⬅️ Back",
        "choose_game": "🎮 Choose a game:",
        "choose_bet": "🪙 Choose your bet:",
        "balance": "💰 Balance",
        "language": "🌍 Choose language:",
        "saved": "✅ Language changed!",
        "admin": "👑 Admin panel",
        "enter_code": "🔐 Enter secret code:",
        "wrong_code": "❌ Wrong code!",
        "admin_ok": "👑 Admin panel opened!",
        "stats": "👥 Users: {users}\n🪙 Total coins: {coins}",
        "no_money": "❌ Not enough coins!",
        "win": "🎉 You won {amount} coins!",
        "lose": "😢 You lost {amount} coins.",
        "profile_text": "👤 Your profile\n\n🆔 ID: {id}\n🪙 Balance: {balance}\n🎮 Games played: {games}",
        "roulette": "🔴 Roulette",
        "slots": "🎰 Slots",
        "dice": "🎲 Dice",
        "coin": "🪙 Coin",
        "number": "🔢 Guess the number",
        "casino_info": "🎰 Game casino\n\nOnly virtual coins are used.",
        "admin_panel": "👑 Administrator panel",
        "cancel": "❌ Cancel"
    }
}

GAME_IDS = ["roulette", "slots", "dice", "coin", "number"]
GAME_NAMES = {
    "roulette": "🔴",
    "slots": "🎰",
    "dice": "🎲",
    "coin": "🪙",
    "number": "🔢"
}

# =========================
# DATABASE
# =========================

def load_data(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

users = load_data(DB_USERS, {})
settings = load_data(DB_SETTINGS, {})
states = {}

def get_user(uid):
    uid = str(uid)

    if uid not in users:
        users[uid] = {
            "balance": 500,
            "language": "ru",
            "games": 0,
            "admin": False
        }
        save_data(DB_USERS, users)

    return users[uid]

def tr(uid, key):
    user = get_user(uid)
    lang = user.get("language", "ru")
    return LANGUAGES.get(lang, LANGUAGES["ru"])[key]

# =========================
# TELEGRAM API
# =========================

def api(method, params=None):
    try:
        data = urllib.parse.urlencode(params or {}).encode()
        req = urllib.request.Request(API_URL + method, data=data)

        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("API error:", e)
        return None

def send(chat, message, keyboard=None):
    params = {
        "chat_id": chat,
        "text": message
    }

    if keyboard:
        params["reply_markup"] = json.dumps(keyboard)

    api("sendMessage", params)

def edit(chat, mid, message, keyboard=None):
    params = {
        "chat_id": chat,
        "message_id": mid,
        "text": message
    }

    if keyboard:
        params["reply_markup"] = json.dumps(keyboard)

    api("editMessageText", params)

def answer(cid, message=None):
    params = {"callback_query_id": cid}
    if message:
        params["text"] = message
        params["show_alert"] = True
    api("answerCallbackQuery", params)

# =========================
# MENUS
# =========================

def main_menu(uid):
    return {
        "inline_keyboard": [
            [{"text": tr(uid, "support"), "url": AUTHOR}],
            [
                {"text": tr(uid, "games"), "callback_data": "games"},
                {"text": tr(uid, "casino"), "callback_data": "casino"}
            ],
            [
                {"text": tr(uid, "settings"), "callback_data": "settings"},
                {"text": tr(uid, "profile"), "callback_data": "profile"}
            ],
            [{"text": tr(uid, "channel"), "url": CHANNEL}]
        ]
    }

def games_menu(uid):
    kb = []

    for game in GAME_IDS:
        kb.append([{
            "text": GAME_NAMES[game] + " " + tr(uid, game),
            "callback_data": "game_" + game
        }])

    kb.append([{
        "text": tr(uid, "back"),
        "callback_data": "home"
    }])

    return {"inline_keyboard": kb}

def settings_menu(uid):
    return {
        "inline_keyboard": [
            [{"text": "🌍 Language / Мова / Тіл", "callback_data": "languages"}],
            [{"text": tr(uid, "admin"), "callback_data": "admin_login"}],
            [{"text": tr(uid, "back"), "callback_data": "home"}]
        ]
    }

def language_menu():
    return {
        "inline_keyboard": [
            [{"text": "🇺🇦 Українська", "callback_data": "lang_uk"}],
            [{"text": "🇷🇺 Русский", "callback_data": "lang_ru"}],
            [{"text": "🇰🇿 Қазақша", "callback_data": "lang_kk"}],
            [{"text": "🇬🇧 English", "callback_data": "lang_en"}],
            [{"text": "⬅️", "callback_data": "settings"}]
        ]
    }

def bet_menu(game):
    return {
        "inline_keyboard": [
            [{"text": f"{n} 🪙", "callback_data": f"bet_{game}_{n}"}]
            for n in [10, 25, 50, 100]
        ] + [[{"text": "⬅️", "callback_data": "games"}]]
    }

# =========================
# GAMES
# =========================

def play_game(game, bet):
    if game == "coin":
        result = random.choice(["heads", "tails"])
        win = result == "heads"
        return win, "🪙 Выпало: " + ("Орёл" if result == "heads" else "Решка")

    if game == "dice":
        player = random.randint(1, 6)
        bot = random.randint(1, 6)
        return player > bot, f"🎲 Ты: {player}\n🤖 Бот: {bot}"

    if game == "roulette":
        number = random.randint(0, 36)
        win = number in [7, 14, 21, 28]
        return win, f"🔴 Выпало число: {number}"

    if game == "slots":
        symbols = ["🍒", "🍋", "🍉", "⭐", "💎"]
        result = [random.choice(symbols) for _ in range(3)]
        win = len(set(result)) == 1
        return win, "🎰 " + " | ".join(result)

    if game == "number":
        secret = random.randint(1, 5)
        guess = random.randint(1, 5)
        return secret == guess, f"🔢 Загадано: {secret}\nТвой результат: {guess}"

    return False, ""

def play(uid, game, bet):
    user = get_user(uid)

    if bet <= 0 or user["balance"] < bet:
        return "no_money"

    win, result = play_game(game, bet)

    user["games"] += 1

    if win:
        # Net profit: + bet
        user["balance"] += bet
        message = tr(uid, "win").format(amount=bet)
    else:
        user["balance"] -= bet
        message = tr(uid, "lose").format(amount=bet)

    save_data(DB_USERS, users)

    return (
        result + "\n\n" + message +
        f"\n\n💰 Баланс: {user['balance']} 🪙"
    )

# =========================
# BOT
# =========================

def run_bot():
    print("BOT STARTED")
    offset = 0

    while True:
        try:
            result = api("getUpdates", {
                "offset": offset + 1,
                "timeout": 20
            })

            if not result or not result.get("ok"):
                time.sleep(2)
                continue

            for update in result["result"]:
                offset = update["update_id"]

                # MESSAGES
                if "message" in update:
                    m = update["message"]
                    uid = str(m["from"]["id"])
                    chat = m["chat"]["id"]
                    txt = m.get("text", "")
                    user = get_user(uid)

                    if txt == "/start":
                        states.pop(uid, None)
                        send(
                            chat,
                            tr(uid, "welcome").format(
                                balance=user["balance"]
                            ),
                            main_menu(uid)
                        )
                        continue

                    state = states.get(uid)

                    if state == "admin_code":
                        states.pop(uid, None)

                        if txt == ADMIN_CODE:
                            user["admin"] = True
                            save_data(DB_USERS, users)

                            total_coins = sum(
                                x.get("balance", 0)
                                for x in users.values()
                            )

                            send(
                                chat,
                                tr(uid, "admin_ok") + "\n\n" +
                                tr(uid, "stats").format(
                                    users=len(users),
                                    coins=total_coins
                                ),
                                settings_menu(uid)
                            )
                        else:
                            send(chat, tr(uid, "wrong_code"),
                                 settings_menu(uid))
                        continue

                    if txt == "/menu":
                        send(chat, "🏠 Menu", main_menu(uid))

                # BUTTONS
                if "callback_query" in update:
                    c = update["callback_query"]
                    uid = str(c["from"]["id"])
                    chat = c["message"]["chat"]["id"]
                    mid = c["message"]["message_id"]
                    d = c["data"]

                    user = get_user(uid)

                    if d == "home":
                        answer(c["id"])
                        edit(
                            chat, mid,
                            tr(uid, "welcome").format(
                                balance=user["balance"]
                            ),
                            main_menu(uid)
                        )

                    elif d == "games" or d == "casino":
                        answer(c["id"])
                        edit(chat, mid, tr(uid, "choose_game"),
                             games_menu(uid))

                    elif d == "settings":
                        answer(c["id"])
                        edit(chat, mid, tr(uid, "settings"),
                             settings_menu(uid))

                    elif d == "languages":
                        answer(c["id"])
                        edit(chat, mid, tr(uid, "language"),
                             language_menu())

                    elif d.startswith("lang_"):
                        lang = d.replace("lang_", "")

                        if lang in LANGUAGES:
                            user["language"] = lang
                            save_data(DB_USERS, users)

                        answer(c["id"], tr(uid, "saved"))
                        edit(
                            chat, mid,
                            tr(uid, "welcome").format(
                                balance=user["balance"]
                            ),
                            main_menu(uid)
                        )

                    elif d == "profile":
                        answer(c["id"])
                        text = tr(uid, "profile_text").format(
                            id=uid,
                            balance=user["balance"],
                            games=user["games"]
                        )
                        edit(chat, mid, text, main_menu(uid))

                    elif d.startswith("game_"):
                        game = d.replace("game_", "")

                        if game in GAME_IDS:
                            answer(c["id"])
                            edit(chat, mid, tr(uid, "choose_bet"),
                                 bet_menu(game))

                    elif d.startswith("bet_"):
                        parts = d.split("_")

                        if len(parts) != 3:
                            continue

                        game = parts[1]
                        bet = int(parts[2])

                        if game not in GAME_IDS:
                            continue

                        if user["balance"] < bet:
                            answer(c["id"], tr(uid, "no_money"))
                            continue

                        answer(c["id"])
                        result_text = play(uid, game, bet)

                        edit(
                            chat, mid,
                            result_text,
                            games_menu(uid)
                        )

                    elif d == "admin_login":
                        answer(c["id"])
                        states[uid] = "admin_code"
                        edit(chat, mid, tr(uid, "enter_code"))

                    elif d == "admin_stats":
                        answer(c["id"])

                        if not user.get("admin"):
                            continue

                        coins = sum(
                            x.get("balance", 0)
                            for x in users.values()
                        )

                        edit(
                            chat, mid,
                            tr(uid, "stats").format(
                                users=len(users),
                                coins=coins
                            ),
                            settings_menu(uid)
                        )

        except Exception as e:
            print("BOT ERROR:", e)
            time.sleep(3)


# =========================
# FLASK / RENDER
# =========================

app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return "Bot is running!", 200

if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def settings_menu(uid):
    kb = [
        [{"text": "🌍 Язык", "callback_data": "languages"}]
    ]

    if get_user(uid).get("admin"):
        kb.append([
            {"text": "📊 Статистика",
             "callback_data": "admin_stats"}
        ])

    kb.extend([
        [{"text": tr(uid, "admin"),
          "callback_data": "admin_login"}],
        [{"text": tr(uid, "back"),
          "callback_data": "home"}]
    ])

    return {"inline_keyboard": kb}
    
