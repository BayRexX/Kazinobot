import random
import json
import os
import time
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
ADMIN_ID = 8642015975
DATA_FILE = "users_data.json"
users = {}
last_update_id = 0

# HTTP сервер для Render
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

# ========== РАБОТА С БАЗОЙ ДАННЫХ ==========
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
    except Exception as e:
        print(f"Load error: {e}")

def init_user(uid, name):
    if uid not in users:
        houses = {1: "коробка", 2: "хижина", 3: "5-этажка", 4: "частный дом", 5: "коттедж у моря"}
        users[uid] = {
            "name": name,
            "balance": 1000,
            "businesses": 0,
            "farms": 0,
            "house": 0,
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

# ========== ОТПРАВКА СООБЩЕНИЙ ==========
def send_message(chat_id, text, reply_markup=None):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        post_data = urllib.parse.urlencode(data).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=post_data))
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

# ========== АДМИН ПАНЕЛЬ С КНОПКАМИ ==========
def admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💰 Изменить баланс", "callback_data": "admin_balance"}],
            [{"text": "🏘️ Изменить дом", "callback_data": "admin_house"}],
            [{"text": "💼 Изменить бизнесы", "callback_data": "admin_business"}],
            [{"text": "🌾 Изменить фермы", "callback_data": "admin_farm"}],
            [{"text": "⚙️ Регулировать прибыль", "callback_data": "admin_profit"}],
            [{"text": "💾 Экспорт БД", "callback_data": "admin_export"}],
            [{"text": "📥 Импорт БД", "callback_data": "admin_import"}]
        ]
    }

def user_admin_keyboard(uid, field, value):
    return {
        "inline_keyboard": [
            [{"text": f"➕ +100", "callback_data": f"admin_add_{uid}_{field}_100"}],
            [{"text": f"➕ +1000", "callback_data": f"admin_add_{uid}_{field}_1000"}],
            [{"text": f"➖ -100", "callback_data": f"admin_sub_{uid}_{field}_100"}],
            [{"text": f"➖ -1000", "callback_data": f"admin_sub_{uid}_{field}_1000"}],
            [{"text": f"✏️ Ввести значение", "callback_data": f"admin_set_{uid}_{field}"}],
            [{"text": "🔙 Назад", "callback_data": "admin_back"}]
        ]
    }

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
            "🏠 /house - купить дом\n"
            "🎲 /casino 100 - сыграть\n"
            "💀 /allin - всё или ничего\n"
            "💼 /business - бизнес (500💰)\n"
            "🌾 /farm - ферма (300💰)\n"
            "📦 /collect - собрать доход\n"
            "🎁 /daily - ежедневный бонус\n"
            "💸 /give 100 - перевод (ответом)\n"
            "🏆 /top - топ игроков")
    
    # PROFILE (свой или чужой)
    elif text == "/profile":
        show_profile(chat_id, user_id)
    elif text.startswith("/profile ") and msg.get("reply_to_message"):
        target_id = msg["reply_to_message"]["from"]["id"]
        init_user(target_id, msg["reply_to_message"]["from"].get("first_name", "User"))
        show_profile(chat_id, target_id)
    
    # BALANCE
    elif text == "/balance":
        send_message(chat_id, f"💰 Ваш баланс: {users[user_id]['balance']}💰")
    
    # HOUSE
    elif text == "/house":
        show_house_menu(chat_id, user_id)
    
    # CASINO
    elif text.startswith("/casino "):
        try:
            bet = int(text.split()[1])
            if bet <= 0 or users[user_id]["balance"] < bet:
                send_message(chat_id, "❌ Не хватает денег!")
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
    
    # COLLECT (ФИКС БАГА - проверка времени)
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
                send_message(chat_id, "⏳ Нет бизнесов, ферм и дома!")
    
    # DAILY
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            send_message(chat_id, "❌ Бонус уже получен! Завтра.")
        else:
            users[user_id]["balance"] += 200
            users[user_id]["last_daily"] = today
            save_users()
            send_message(chat_id, f"🎁 БОНУС! +200💰\n💰 Баланс: {users[user_id]['balance']}💰")
    
    # GIVE
    elif text.startswith("/give "):
        if "reply_to_message" not in msg:
            send_message(chat_id, "❌ Ответьте на сообщение человека!")
            return
        try:
            amount = int(text.split()[1])
            receiver_id = msg["reply_to_message"]["from"]["id"]
            receiver_name = msg["reply_to_message"]["from"].get("first_name", "User")
            if amount <= 0 or users[user_id]["balance"] < amount:
                send_message(chat_id, "❌ Не хватает денег!")
            else:
                init_user(receiver_id, receiver_name)
                users[user_id]["balance"] -= amount
                users[receiver_id]["balance"] += amount
                save_users()
                send_message(chat_id, f"✅ Переведено {amount}💰 {receiver_name}")
        except:
            send_message(chat_id, "💸 /give 100 (ответом на сообщение)")
    
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
    
    # ADMIN
    elif text == "/admin" and user_id == ADMIN_ID:
        send_message(chat_id, "👑 АДМИН ПАНЕЛЬ 👑\n\nВыберите действие:", admin_keyboard())

def show_profile(chat_id, user_id):
    u = users[user_id]
    house = get_house_info(u['house_level'])
    
    # Время до следующего бонуса
    daily_time = "Сегодня уже получен" if u["last_daily"] == datetime.now().date() else "Доступен"
    if u["last_daily"] and u["last_daily"] != datetime.now().date():
        daily_time = "Доступен"
    
    # Доход в час
    hourly_income = u["businesses"] * 50 + u["farms"] * 30 + house["income"]
    
    msg = (
        f"👤 <b>{u['name']}</b>\n\n"
        f"💰 Баланс: {u['balance']}💰\n"
        f"🏠 Дом: {house['name']} (+{house['income']}💰/час)\n"
        f"💼 Бизнесов: {u['businesses']} (50💰/час)\n"
        f"🌾 Ферм: {u['farms']} (30💰/час)\n"
        f"📊 Общий доход в час: {hourly_income}💰\n"
        f"🎁 Ежедневный бонус: {daily_time}\n"
        f"⏳ Последний сбор: {datetime.fromtimestamp(u.get('last_collect', time.time())).strftime('%H:%M:%S')}"
    )
    send_message(chat_id, msg)

def show_house_menu(chat_id, user_id):
    current_house = get_house_info(users[user_id]['house_level'])
    keyboard = {"inline_keyboard": []}
    
    for level in range(1, 6):
        house = get_house_info(level)
        if level > users[user_id]['house_level']:
            keyboard["inline_keyboard"].append([
                {"text": f"🏠 {house['name']} - {house['price']}💰", "callback_data": f"buy_house_{level}"}
            ])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "back_menu"}])
    
    msg = f"🏠 <b>Ваш дом:</b> {current_house['name']}\n💵 Доход: +{current_house['income']}💰/час\n\nДоступные дома для покупки:"
    send_message(chat_id, msg, keyboard)

# ========== ОБРАБОТКА CALLBACK ==========
def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback["data"]
    
    # Покупка дома
    if data.startswith("buy_house_"):
        level = int(data.split("_")[2])
        house = get_house_info(level)
        if users[user_id]["balance"] >= house["price"] and level == users[user_id]["house_level"] + 1:
            users[user_id]["balance"] -= house["price"]
            users[user_id]["house_level"] = level
            save_users()
            send_message(chat_id, f"✅ Поздравляю! Вы купили {house['name']}!\n💰 Остаток: {users[user_id]['balance']}💰")
        else:
            send_message(chat_id, "❌ Не хватает денег или нужно покупать дома по порядку!")
        show_house_menu(chat_id, user_id)
    
    # АДМИН КНОПКИ
    elif data == "admin_balance" and user_id == ADMIN_ID:
        send_message(chat_id, "👑 Выберите пользователя (ответьте на его сообщение командой /admin_set_balance)")
    
    elif data == "admin_back" and user_id == ADMIN_ID:
        send_message(chat_id, "👑 АДМИН ПАНЕЛЬ", admin_keyboard())

def main():
    global last_update_id
    load_users()
    print("🤖 Бот запущен!")
    print("✅ HTTP сервер на порту 10000 запущен")
    
    while True:
        try:
            updates = get_updates(last_update_id + 1)
            if updates.get("ok"):
                for update in updates.get("result", []):
                    if "message" in update:
                        handle_message(update["message"])
                    if "callback_query" in update:
                        handle_callback(update["callback_query"])
                    last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
