import random
import json
import os
import time
import threading
import string
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
ADMIN_ID = 8642015975
DATA_FILE = "users_data.json"
PROMO_FILE = "promocodes.json"
users = {}
promocodes = {}
last_update_id = 0

# ========== HTTP СЕРВЕР ДЛЯ RENDER ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# ========== РАБОТА С БАЗОЙ ПОЛЬЗОВАТЕЛЕЙ ==========
def save_users():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            data = {}
            for uid, u in users.items():
                data[str(uid)] = u.copy()
                if data[str(uid)].get("last_daily"):
                    data[str(uid)]["last_daily"] = data[str(uid)]["last_daily"].isoformat()
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Данные сохранены")
    except Exception as e:
        print(f"Save error: {e}")

def load_users():
    global users
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for uid, u in data.items():
                if u.get("last_daily"):
                    u["last_daily"] = datetime.fromisoformat(u["last_daily"])
                users[int(uid)] = u
            print(f"✅ Загружено {len(users)} пользователей")
        else:
            print("📁 Новый файл пользователей")
    except Exception as e:
        print(f"Load error: {e}")

def init_user(uid, name):
    if uid not in users:
        users[uid] = {
            "name": name,
            "balance": 1000,
            "businesses": 0,
            "farms": 0,
            "house_level": 0,
            "last_daily": None,
            "last_collect": time.time()
        }
        save_users()

def get_house_info(level):
    houses = {
        0: {"name": "Бездомный", "income": 0, "price": 0},
        1: {"name": "📦 Коробка", "income": 10, "price": 100},
        2: {"name": "🏚️ Хижина", "income": 30, "price": 500},
        3: {"name": "🏢 5-этажка", "income": 80, "price": 1200},
        4: {"name": "🏠 Частный дом", "income": 150, "price": 3500},
        5: {"name": "🏖️ Коттедж у моря", "income": 300, "price": 6800}
    }
    return houses[level]

# ========== РАБОТА С ПРОМОКОДАМИ ==========
def save_promocodes():
    try:
        with open(PROMO_FILE, 'w', encoding='utf-8') as f:
            json.dump(promocodes, f, ensure_ascii=False, indent=2)
        print("✅ Промокоды сохранены")
    except Exception as e:
        print(f"Save promocodes error: {e}")

def load_promocodes():
    global promocodes
    try:
        if os.path.exists(PROMO_FILE):
            with open(PROMO_FILE, 'r', encoding='utf-8') as f:
                promocodes = json.load(f)
            print(f"✅ Загружено {len(promocodes)} промокодов")
        else:
            print("📁 Новый файл промокодов")
    except Exception as e:
        print(f"Load promocodes error: {e}")

def generate_promocode():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

# ========== ОТПРАВКА СООБЩЕНИЙ ==========
def send_message(chat_id, text):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        post_data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=post_data, method="POST")
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Send error: {e}")

def get_updates(offset):
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Get updates error: {e}")
        return {"ok": False, "result": []}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def show_profile(chat_id, user_id):
    u = users[user_id]
    house = get_house_info(u['house_level'])
    hourly_income = u["businesses"] * 50 + u["farms"] * 30 + house["income"]
    
    next_house = ""
    if u['house_level'] < 5:
        next_h = get_house_info(u['house_level'] + 1)
        next_house = f"\n🏠 След. дом: {next_h['name']} - {next_h['price']}💰"
    
    msg = (
        f"👤 <b>{u['name']}</b>\n\n"
        f"💰 Баланс: {u['balance']}💰\n"
        f"🏠 Дом: {house['name']} (+{house['income']}💰/ч){next_house}\n"
        f"💼 Бизнесов: {u['businesses']} (+{u['businesses']*50}💰/ч)\n"
        f"🌾 Ферм: {u['farms']} (+{u['farms']*30}💰/ч)\n"
        f"📊 Доход в час: {hourly_income}💰\n"
        f"📦 /collect - собрать доход"
    )
    send_message(chat_id, msg)

def show_house_menu(chat_id, user_id):
    current = get_house_info(users[user_id]['house_level'])
    msg = f"🏠 <b>Ваш дом:</b> {current['name']} (+{current['income']}💰/час)\n\n"
    
    if users[user_id]['house_level'] >= 5:
        msg += "🎉 У вас максимальный дом!\n"
    else:
        msg += "📋 Доступные дома:\n\n"
        for level in range(users[user_id]['house_level'] + 1, 6):
            house = get_house_info(level)
            msg += f"{level}. {house['name']} — {house['price']}💰\n"
        msg += "\n💡 Купить: /house 1 (цифра от 1 до 5)"
    
    send_message(chat_id, msg)

def buy_house(chat_id, user_id, level):
    if users[user_id]['house_level'] + 1 != level:
        send_message(chat_id, f"❌ Нужно покупать дома по порядку! Следующий дом: /house {users[user_id]['house_level'] + 1}")
        return
    
    house = get_house_info(level)
    if users[user_id]["balance"] >= house["price"]:
        users[user_id]["balance"] -= house["price"]
        users[user_id]["house_level"] = level
        save_users()
        send_message(chat_id, f"🏠 ПОЗДРАВЛЯЮ!\nВы купили {house['name']}!\n💰 Остаток: {users[user_id]['balance']}💰")
    else:
        send_message(chat_id, f"❌ Не хватает! Нужно {house['price']}💰, у вас {users[user_id]['balance']}💰")

# ========== ОБРАБОТКА КОМАНД ==========
def handle_message(msg):
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    user_name = msg["from"].get("first_name", "User")
    text = msg.get("text", "")
    
    init_user(user_id, user_name)
    
    # START
    if text == "/start":
        send_message(chat_id,
            "🎰 КАЗИНО БОТ 🎰\n\n"
            "💰 /balance - баланс\n"
            "👤 /profile - профиль\n"
            "👤 /profile (ответом) - профиль другого\n"
            "🏠 /house - купить дом\n"
            "🏠 /house 1-5 - купить конкретный дом\n"
            "🎲 /casino 100 - сыграть\n"
            "💀 /allin - всё или ничего\n"
            "💼 /business - бизнес (500💰)\n"
            "🌾 /farm - ферма (300💰)\n"
            "📦 /collect - собрать доход\n"
            "🎁 /daily - бонус\n"
            "💸 /give 100 (ответом) - перевод\n"
            "🎫 /promo КОД - активировать промокод\n"
            "🏆 /top - топ\n"
    
    # PROFILE
    elif text == "/profile":
        show_profile(chat_id, user_id)
    elif text.startswith("/profile") and msg.get("reply_to_message"):
        target_id = msg["reply_to_message"]["from"]["id"]
        init_user(target_id, msg["reply_to_message"]["from"].get("first_name", "User"))
        show_profile(chat_id, target_id)
    
    # BALANCE
    elif text == "/balance":
        send_message(chat_id, f"💰 Баланс: {users[user_id]['balance']}💰")
    
    # HOUSE
    elif text == "/house":
        show_house_menu(chat_id, user_id)
    elif text.startswith("/house "):
        try:
            level = int(text.split()[1])
            if 1 <= level <= 5:
                buy_house(chat_id, user_id, level)
            else:
                send_message(chat_id, "🏠 Используй: /house 1-5\n1-Коробка 2-Хижина 3-5этажка 4-Частный дом 5-Коттедж")
        except:
            send_message(chat_id, "🏠 /house 1-5")
    
    # CASINO
    elif text.startswith("/casino "):
        try:
            parts = text.split()
            if len(parts) != 2:
                send_message(chat_id, "🎲 /casino 100")
                return
            bet = int(parts[1])
            if bet <= 0:
                send_message(chat_id, "❌ Ставка > 0!")
            elif users[user_id]["balance"] < bet:
                send_message(chat_id, f"❌ Не хватает! У вас {users[user_id]['balance']}💰")
            else:
                if random.random() < 0.45:
                    win = bet * 2
                    users[user_id]["balance"] += win
                    save_users()
                    send_message(chat_id, f"🎉 ВЫИГРЫШ! +{win}💰\n💰 Баланс: {users[user_id]['balance']}💰")
                else:
                    users[user_id]["balance"] -= bet
                    save_users()
                    send_message(chat_id, f"😞 ПРОИГРЫШ! -{bet}💰\n💰 Баланс: {users[user_id]['balance']}💰")
        except:
            send_message(chat_id, "🎲 /casino 100")
    
    # ALLIN
    elif text == "/allin":
        bet = users[user_id]["balance"]
        if bet <= 0:
            send_message(chat_id, "❌ Нечем рисковать!")
        else:
            if random.random() < 0.4:
                users[user_id]["balance"] *= 2
                save_users()
                send_message(chat_id, f"💀🔥 УДВОИЛИ! Баланс: {users[user_id]['balance']}💰")
            else:
                users[user_id]["balance"] = 0
                save_users()
                send_message(chat_id, f"💀😭 ПРОИГРАЛИ ВСЁ! Баланс: 0💰")
    
    # BUSINESS
    elif text == "/business":
        if users[user_id]["balance"] >= 500:
            users[user_id]["balance"] -= 500
            users[user_id]["businesses"] += 1
            save_users()
            send_message(chat_id, f"✅ Бизнес куплен! -500💰\nДоход: 50💰/час")
        else:
            send_message(chat_id, f"❌ Нужно 500💰, у вас {users[user_id]['balance']}💰")
    
    # FARM
    elif text == "/farm":
        if users[user_id]["balance"] >= 300:
            users[user_id]["balance"] -= 300
            users[user_id]["farms"] += 1
            save_users()
            send_message(chat_id, f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
        else:
            send_message(chat_id, f"❌ Нужно 300💰, у вас {users[user_id]['balance']}💰")
    
    # COLLECT (ФИКС БАГА)
    elif text == "/collect":
        now = time.time()
        if 'last_collect' not in users[user_id]:
            users[user_id]['last_collect'] = now
        
        hours = (now - users[user_id]['last_collect']) // 3600
        
        if hours < 1:
            remaining = 3600 - (now - users[user_id]['last_collect'])
            minutes = int(remaining // 60)
            send_message(chat_id, f"⏳ До следующего сбора: {minutes} минут")
        else:
            house_income = get_house_info(users[user_id]['house_level'])["income"]
            total = users[user_id]["businesses"] * 50 + users[user_id]["farms"] * 30 + house_income
            total = int(total * hours)
            if total > 0:
                users[user_id]["balance"] += total
                users[user_id]['last_collect'] = now
                save_users()
                send_message(chat_id, f"📦 Собрано {total}💰 за {int(hours)} час(ов)!\n💰 Баланс: {users[user_id]['balance']}💰")
            else:
                send_message(chat_id, "⏳ Нет бизнесов, ферм и дома! Купи /business, /farm, /house")
    
    # DAILY
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            send_message(chat_id, "❌ Бонус уже получен! Завтра.")
        else:
            bonus = 200 + users[user_id]["house_level"] * 50
            users[user_id]["balance"] += bonus
            users[user_id]["last_daily"] = today
            save_users()
            send_message(chat_id, f"🎁 ЕЖЕДНЕВНЫЙ БОНУС! +{bonus}💰\n💰 Баланс: {users[user_id]['balance']}💰")
    
    # GIVE
    elif text.startswith("/give "):
        if "reply_to_message" not in msg:
            send_message(chat_id, "❌ Ответьте на сообщение человека, которому хотите перевести!")
            return
        try:
            parts = text.split()
            if len(parts) != 2:
                send_message(chat_id, "💸 /give 100")
                return
            amount = int(parts[1])
            receiver_id = msg["reply_to_message"]["from"]["id"]
            receiver_name = msg["reply_to_message"]["from"].get("first_name", "User")
            if amount <= 0:
                send_message(chat_id, "❌ Сумма > 0!")
            elif users[user_id]["balance"] < amount:
                send_message(chat_id, f"❌ Не хватает! У вас {users[user_id]['balance']}💰")
            else:
                init_user(receiver_id, receiver_name)
                users[user_id]["balance"] -= amount
                users[receiver_id]["balance"] += amount
                save_users()
                send_message(chat_id, f"✅ Переведено {amount}💰 {receiver_name}")
                send_message(receiver_id, f"💰 {user_name} перевёл(а) вам {amount}💰!\nБаланс: {users[receiver_id]['balance']}💰")
        except:
            send_message(chat_id, "💸 /give 100")
    
    # TOP
    elif text == "/top":
        if not users:
            send_message(chat_id, "Нет игроков")
        else:
            sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
            result = "🏆 ТОП ПО БАЛАНСУ 🏆\n\n"
            for i, (uid, data) in enumerate(sorted_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                result += f"{medal} {data['name']} — {data['balance']}💰\n"
            send_message(chat_id, result)
    
    # PROMO (активация для всех)
    elif text.startswith("/promo "):
        parts = text.split()
        if len(parts) != 2:
            send_message(chat_id, "🎫 /promo [код]\n\nПример: /promo ABC12345")
            return
        
        code = parts[1].upper()
        
        if code not in promocodes:
            send_message(chat_id, f"❌ Промокод {code} не найден!")
            return
        
        promo = promocodes[code]
        
        if promo["used"] >= promo["max_uses"]:
            send_message(chat_id, f"❌ Промокод {code} уже использован максимальное количество раз!")
            return
        
        if str(user_id) in promo["used_by"]:
            send_message(chat_id, "❌ Вы уже активировали этот промокод!")
            return
        
        promo["used"] += 1
        promo["used_by"].append(str(user_id))
        users[user_id]["balance"] += promo["amount"]
        save_users()
        save_promocodes()
        
        remaining = promo["max_uses"] - promo["used"]
        send_message(chat_id, f"🎉 ПРОМОКОД АКТИВИРОВАН!\n\n💰 +{promo['amount']}💰\n📊 Осталось активаций: {remaining}\n💰 Ваш баланс: {users[user_id]['balance']}💰")
    
    # ========== АДМИН КОМАНДЫ ==========
    elif text == "/admin" and user_id == ADMIN_ID:
        send_message(chat_id,
            "👑 АДМИН ПАНЕЛЬ 👑\n\n"
            f"📊 Статистика:\n"
            f"👥 Всего игроков: {len(users)}\n"
            f"🎫 Промокодов: {len(promocodes)}\n\n"
            "🔧 Команды:\n"
            "/admin_balance [ID] [сумма] - изменить баланс\n"
            "/admin_house [ID] [1-5] - изменить дом\n"
            "/admin_business [ID] [+/-] - бизнесы\n"
            "/admin_farm [ID] [+/-] - фермы\n"
            "/admin_top - топ игроков\n"
            "/admin_list - список игроков\n"
            "/admin_export - экспорт БД\n"
            "/createpromo [сумма] [активации] - создать промокод\n"
            "/listpromo - список промокодов\n"
            "/delpromo [код] - удалить промокод\n"
            "/admin_help - подробная помощь")
    
    elif text == "/admin_help" and user_id == ADMIN_ID:
        send_message(chat_id,
            "📖 АДМИН КОМАНДЫ:\n\n"
            "💰 БАЛАНС:\n"
            "/admin_balance 123456 500 - добавить 500💰\n"
            "/admin_balance 123456 -500 - отнять 500💰\n"
            "/admin_balance 123456 =1000 - установить 1000💰\n\n"
            "🏠 ДОМ:\n"
            "/admin_house 123456 3 - установить дом (0-5)\n\n"
            "💼 БИЗНЕС:\n"
            "/admin_business 123456 + - добавить бизнес\n"
            "/admin_business 123456 - - убрать бизнес\n\n"
            "🌾 ФЕРМА:\n"
            "/admin_farm 123456 + - добавить ферму\n"
            "/admin_farm 123456 - - убрать ферму\n\n"
            "🎫 ПРОМОКОДЫ:\n"
            "/createpromo 500 10 - создать промокод\n"
            "/listpromo - список промокодов\n"
            "/delpromo ABC12345 - удалить промокод\n\n"
            "📊 ПРОЧЕЕ:\n"
            "/admin_top - топ 10 по балансу\n"
            "/admin_list - список игроков с ID\n"
            "/admin_export - экспорт БД в JSON")
    
    elif text == "/admin_top" and user_id == ADMIN_ID:
        if not users:
            send_message(chat_id, "Нет игроков")
        else:
            sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
            result = "🏆 ТОП ИГРОКОВ (АДМИН) 🏆\n\n"
            for i, (uid, data) in enumerate(sorted_users, 1):
                result += f"{i}. {data['name']} (ID:{uid}) — {data['balance']}💰\n"
            send_message(chat_id, result)
    
    elif text == "/admin_list" and user_id == ADMIN_ID:
        if not users:
            send_message(chat_id, "Нет игроков")
        else:
            result = "📋 СПИСОК ИГРОКОВ:\n\n"
            for uid, data in list(users.items())[:30]:
                result += f"👤 {data['name']} — ID: {uid}\n"
            if len(users) > 30:
                result += f"\n... и ещё {len(users)-30} игроков"
            send_message(chat_id, result)
    
    elif text == "/admin_export" and user_id == ADMIN_ID:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                backup = f.read()
            if len(backup) > 4000:
                backup = backup[:4000] + "\n... (файл слишком большой, обрезано)"
            send_message(chat_id, f"💾 ЭКСПОРТ БД:\n\n<code>{backup}</code>")
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка: {e}")
    
    elif text.startswith("/admin_balance") and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "⚠️ /admin_balance [ID] [сумма]\nПример: /admin_balance 123456 500\nПример: /admin_balance 123456 -500\nПример: /admin_balance 123456 =1000")
            return
        try:
            target_id = int(parts[1])
            amount_str = parts[2]
            
            if target_id not in users:
                send_message(chat_id, f"❌ Пользователь с ID {target_id} не найден!")
                return
            
            if amount_str.startswith("="):
                new_balance = int(amount_str[1:])
                old_balance = users[target_id]["balance"]
                users[target_id]["balance"] = new_balance
                save_users()
                send_message(chat_id, f"✅ Баланс {users[target_id]['name']} изменён:\n{old_balance}💰 → {new_balance}💰")
            else:
                amount = int(amount_str)
                old_balance = users[target_id]["balance"]
                users[target_id]["balance"] += amount
                if users[target_id]["balance"] < 0:
                    users[target_id]["balance"] = 0
                save_users()
                if amount > 0:
                    send_message(chat_id, f"✅ +{amount}💰 {users[target_id]['name']}\n{old_balance}💰 → {users[target_id]['balance']}💰")
                else:
                    send_message(chat_id, f"✅ {amount}💰 {users[target_id]['name']}\n{old_balance}💰 → {users[target_id]['balance']}💰")
        except:
            send_message(chat_id, "❌ Ошибка! /admin_balance [ID] [сумма]")
    
    elif text.startswith("/admin_house") and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "⚠️ /admin_house [ID] [1-5]\nПример: /admin_house 123456 3")
            return
        try:
            target_id = int(parts[1])
            level = int(parts[2])
            
            if target_id not in users:
                send_message(chat_id, f"❌ Пользователь с ID {target_id} не найден!")
                return
            if level < 0 or level > 5:
                send_message(chat_id, "❌ Уровень дома должен быть от 0 до 5!")
                return
            
            old_house = get_house_info(users[target_id]["house_level"])
            users[target_id]["house_level"] = level
            new_house = get_house_info(level)
            save_users()
            send_message(chat_id, f"✅ Дом {users[target_id]['name']} изменён:\n{old_house['name']} → {new_house['name']}")
        except:
            send_message(chat_id, "❌ Ошибка! /admin_house [ID] [1-5]")
    
    elif text.startswith("/admin_business") and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "⚠️ /admin_business [ID] [+/-]\nПример: /admin_business 123456 +\nПример: /admin_business 123456 -")
            return
        try:
            target_id = int(parts[1])
            action = parts[2]
            
            if target_id not in users:
                send_message(chat_id, f"❌ Пользователь с ID {target_id} не найден!")
                return
            
            if action == "+":
                users[target_id]["businesses"] += 1
                save_users()
                send_message(chat_id, f"✅ +1 бизнес {users[target_id]['name']}\nВсего: {users[target_id]['businesses']}")
            elif action == "-":
                users[target_id]["businesses"] = max(0, users[target_id]["businesses"] - 1)
                save_users()
                send_message(chat_id, f"✅ -1 бизнес {users[target_id]['name']}\nВсего: {users[target_id]['businesses']}")
            else:
                send_message(chat_id, "❌ Используй + или -")
        except:
            send_message(chat_id, "❌ Ошибка! /admin_business [ID] [+/-]")
    
    elif text.startswith("/admin_farm") and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "⚠️ /admin_farm [ID] [+/-]\nПример: /admin_farm 123456 +\nПример: /admin_farm 123456 -")
            return
        try:
            target_id = int(parts[1])
            action = parts[2]
            
            if target_id not in users:
                send_message(chat_id, f"❌ Пользователь с ID {target_id} не найден!")
                return
            
            if action == "+":
                users[target_id]["farms"] += 1
                save_users()
                send_message(chat_id, f"✅ +1 ферма {users[target_id]['name']}\nВсего: {users[target_id]['farms']}")
            elif action == "-":
                users[target_id]["farms"] = max(0, users[target_id]["farms"] - 1)
                save_users()
                send_message(chat_id, f"✅ -1 ферма {users[target_id]['name']}\nВсего: {users[target_id]['farms']}")
            else:
                send_message(chat_id, "❌ Используй + или -")
        except:
            send_message(chat_id, "❌ Ошибка! /admin_farm [ID] [+/-]")
    
    # ========== СОЗДАНИЕ ПРОМОКОДА (АДМИН) ==========
    elif text.startswith("/createpromo") and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 3:
            send_message(chat_id, "🎫 /createpromo [сумма] [активации]\n\nПример: /createpromo 500 10")
            return
        try:
            amount = int(parts[1])
            max_uses = int(parts[2])
            
            if amount <= 0:
                send_message(chat_id, "❌ Сумма > 0!")
                return
            if max_uses <= 0:
                send_message(chat_id, "❌ Активаций > 0!")
                return
            
            code = generate_promocode()
            promocodes[code] = {
                "amount": amount,
                "max_uses": max_uses,
                "used": 0,
                "used_by": [],
                "created_by": user_id,
                "created_at": datetime.now().isoformat()
            }
            save_promocodes()
            send_message(chat_id, f"✅ ПРОМОКОД СОЗДАН!\n\n🎫 Код: <code>{code}</code>\n💰 Сумма: {amount}💰\n🔄 Активаций: {max_uses}\n\nИспользовать: /promo {code}")
        except:
            send_message(chat_id, "❌ Ошибка! /createpromo 500 10")
    
    elif text.startswith("/delpromo") and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 2:
            send_message(chat_id, "🗑️ /delpromo [код]\n\nПример: /delpromo ABC12345")
            return
        code = parts[1].upper()
        if code in promocodes:
            del promocodes[code]
            save_promocodes()
            send_message(chat_id, f"✅ Промокод {code} удалён!")
        else:
            send_message(chat_id, f"❌ Промокод {code} не найден!")
    
    elif text == "/listpromo" and user_id == ADMIN_ID:
        if not promocodes:
            send_message(chat_id, "📭 Нет активных промокодов")
            return
        
        msg = "🎫 АКТИВНЫЕ ПРОМОКОДЫ 🎫\n\n"
        for code, data in promocodes.items():
            remaining = data["max_uses"] - data["used"]
            msg += f"<code>{code}</code> — {data['amount']}💰, осталось: {remaining}/{data['max_uses']}\n"
        send_message(chat_id, msg)

def main():
    global last_update_id
    load_users()
    load_promocodes()
    print("=" * 40)
    print("🤖 БОТ КАЗИНО ЗАПУЩЕН!")
    print(f"👑 АДМИН ID: {ADMIN_ID}")
    print(f"👥 ПОЛЬЗОВАТЕЛЕЙ: {len(users)}")
    print(f"🎫 ПРОМОКОДОВ: {len(promocodes)}")
    print("=" * 40)
    
    while True:
        try:
            updates = get_updates(last_update_id + 1)
            if updates.get("ok"):
                for update in updates.get("result", []):
                    if "message" in update:
                        handle_message(update["message"])
                    if update["update_id"] > last_update_id:
                        last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
