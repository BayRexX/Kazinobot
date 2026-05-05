import random
import json
import os
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
ADMIN_ID = 8642015975
DATA_FILE = "users_data.json"
users = {}
last_update_id = 0
admin_temp_data = {}

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

def edit_message(chat_id, message_id, text, reply_markup=None):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        post_data = urllib.parse.urlencode(data).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=post_data))
    except Exception as e:
        print(f"Edit error: {e}")

def get_updates(offset):
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Get updates error: {e}")
        return {"ok": False, "result": []}

# ========== КЛАВИАТУРЫ ==========
def admin_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💰 Изменить баланс", "callback_data": "admin_balance"}],
            [{"text": "🏠 Изменить дом", "callback_data": "admin_house"}],
            [{"text": "💼 Изменить бизнесы", "callback_data": "admin_business"}],
            [{"text": "🌾 Изменить фермы", "callback_data": "admin_farm"}],
            [{"text": "⚙️ Регулировать прибыль", "callback_data": "admin_profit"}],
            [{"text": "💾 Экспорт БД", "callback_data": "admin_export"}],
            [{"text": "📥 Импорт БД", "callback_data": "admin_import"}]
        ]
    }

def admin_user_selection_keyboard(action):
    keyboard = {"inline_keyboard": []}
    for uid, u in list(users.items())[:20]:
        keyboard["inline_keyboard"].append([
            {"text": f"👤 {u['name']} (ID: {uid})", "callback_data": f"admin_select_{action}_{uid}"}
        ])
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "admin_back"}])
    return keyboard

def admin_edit_keyboard(uid, field, current_value):
    return {
        "inline_keyboard": [
            [{"text": "➕ +100", "callback_data": f"admin_add_{field}_{uid}_100"}],
            [{"text": "➕ +1000", "callback_data": f"admin_add_{field}_{uid}_1000"}],
            [{"text": "➖ -100", "callback_data": f"admin_sub_{field}_{uid}_100"}],
            [{"text": "➖ -1000", "callback_data": f"admin_sub_{field}_{uid}_1000"}],
            [{"text": "✏️ Ввести значение", "callback_data": f"admin_set_{field}_{uid}"}],
            [{"text": "🔙 Назад", "callback_data": f"admin_back_select_{field}"}]
        ]
    }

def house_buy_keyboard(current_level):
    keyboard = {"inline_keyboard": []}
    for level in range(1, 6):
        house = get_house_info(level)
        if level > current_level:
            keyboard["inline_keyboard"].append([
                {"text": f"🏠 {house['name']} - {house['price']}💰", "callback_data": f"buy_house_{level}"}
            ])
        else:
            keyboard["inline_keyboard"].append([
                {"text": f"✅ {house['name']} (уже куплен)", "callback_data": "noop"}
            ])
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "back_menu"}])
    return keyboard

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
            "🎁 /daily - бонус\n"
            "💸 /give 100 - перевод\n"
            "🏆 /top - топ")
    
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
            send_message(chat_id, f"❌ Нужно 500💰")
    
    # FARM
    elif text == "/farm":
        if users[user_id]["balance"] >= 300:
            users[user_id]["balance"] -= 300
            users[user_id]["farms"] += 1
            save_users()
            send_message(chat_id, f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
        else:
            send_message(chat_id, f"❌ Нужно 300💰")
    
    # COLLECT
    elif text == "/collect":
        now = time.time()
        if 'last_collect' not in users[user_id]:
            users[user_id]['last_collect'] = now
        
        hours = (now - users[user_id]['last_collect']) // 3600
        
        if hours < 1:
            remaining = 3600 - (now - users[user_id]['last_collect'])
            minutes = int(remaining // 60)
            send_message(chat_id, f"⏳ До сбора: {minutes} мин")
        else:
            house_income = get_house_info(users[user_id]['house_level'])["income"]
            total = users[user_id]["businesses"] * 50 + users[user_id]["farms"] * 30 + house_income
            total = int(total * hours)
            if total > 0:
                users[user_id]["balance"] += total
                users[user_id]['last_collect'] = now
                save_users()
                send_message(chat_id, f"📦 +{total}💰 за {int(hours)} ч!\n💰 Баланс: {users[user_id]['balance']}💰")
            else:
                send_message(chat_id, "⏳ Нет бизнесов, ферм и дома!")
    
    # DAILY
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            send_message(chat_id, "❌ Бонус уже получен!")
        else:
            users[user_id]["balance"] += 200
            users[user_id]["last_daily"] = today
            save_users()
            send_message(chat_id, f"🎁 +200💰! Баланс: {users[user_id]['balance']}💰")
    
    # GIVE
    elif text.startswith("/give "):
        if "reply_to_message" not in msg:
            send_message(chat_id, "❌ Ответьте на сообщение!")
            return
        try:
            amount = int(text.split()[1])
            receiver_id = msg["reply_to_message"]["from"]["id"]
            receiver_name = msg["reply_to_message"]["from"].get("first_name", "User")
            if amount <= 0 or users[user_id]["balance"] < amount:
                send_message(chat_id, "❌ Не хватает!")
            else:
                init_user(receiver_id, receiver_name)
                users[user_id]["balance"] -= amount
                users[receiver_id]["balance"] += amount
                save_users()
                send_message(chat_id, f"✅ Переведено {amount}💰 {receiver_name}")
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
    
    # ADMIN
    elif text == "/admin" and user_id == ADMIN_ID:
        send_message(chat_id, "👑 АДМИН ПАНЕЛЬ 👑", admin_main_keyboard())

def show_profile(chat_id, user_id):
    u = users[user_id]
    house = get_house_info(u['house_level'])
    hourly_income = u["businesses"] * 50 + u["farms"] * 30 + house["income"]
    daily_status = "Доступен" if u["last_daily"] != datetime.now().date() else "Уже получен"
    
    msg = (
        f"👤 <b>{u['name']}</b>\n\n"
        f"💰 Баланс: {u['balance']}💰\n"
        f"🏠 Дом: {house['name']} (+{house['income']}💰/ч)\n"
        f"💼 Бизнесов: {u['businesses']} (+50💰/ч)\n"
        f"🌾 Ферм: {u['farms']} (+30💰/ч)\n"
        f"📊 Доход в час: {hourly_income}💰\n"
        f"🎁 Бонус: {daily_status}"
    )
    send_message(chat_id, msg)

def show_house_menu(chat_id, user_id):
    current_level = users[user_id]['house_level']
    current_house = get_house_info(current_level)
    keyboard = house_buy_keyboard(current_level)
    msg = f"🏠 Ваш дом: {current_house['name']} (+{current_house['income']}💰/ч)\n\nДоступные дома:"
    send_message(chat_id, msg, keyboard)

# ========== ОБРАБОТКА CALLBACK ==========
def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    user_id = callback["from"]["id"]
    data = callback["data"]
    
    # Покупка дома
    if data.startswith("buy_house_"):
        level = int(data.split("_")[2])
        house = get_house_info(level)
        if users[user_id]["house_level"] + 1 == level and users[user_id]["balance"] >= house["price"]:
            users[user_id]["balance"] -= house["price"]
            users[user_id]["house_level"] = level
            save_users()
            edit_message(chat_id, message_id, f"✅ Куплен {house['name']}!\n💰 Остаток: {users[user_id]['balance']}💰")
        else:
            edit_message(chat_id, message_id, "❌ Не хватает денег или нужно покупать по порядку!")
        show_house_menu(chat_id, user_id)
        return
    
    if data == "back_menu":
        show_house_menu(chat_id, user_id)
        return
    
    # АДМИН КНОПКИ
    if user_id != ADMIN_ID:
        return
    
    # Главное меню
    if data == "admin_balance":
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_selection_keyboard("balance"))
    elif data == "admin_house":
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_selection_keyboard("house"))
    elif data == "admin_business":
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_selection_keyboard("business"))
    elif data == "admin_farm":
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_selection_keyboard("farm"))
    elif data == "admin_profit":
        edit_message(chat_id, message_id, "⚙️ Регулировка прибыли пока в разработке")
    elif data == "admin_export":
        try:
            with open(DATA_FILE, 'r') as f:
                backup_data = f.read()
            send_message(chat_id, f"💾 Бэкап БД:\n<code>{backup_data[:3000]}</code>")
        except:
            send_message(chat_id, "❌ Ошибка экспорта")
    elif data == "admin_import":
        send_message(chat_id, "📥 Отправьте JSON файл с данными")
        admin_temp_data[user_id] = "waiting_import"
    elif data == "admin_back":
        edit_message(chat_id, message_id, "👑 АДМИН ПАНЕЛЬ", admin_main_keyboard())
    
    # Выбор пользователя
    elif data.startswith("admin_select_"):
        parts = data.split("_")
        action = parts[2]
        target_uid = int(parts[3])
        target_name = users[target_uid]["name"]
        
        if action == "balance":
            edit_message(chat_id, message_id, f"👤 {target_name}\n💰 Баланс: {users[target_uid]['balance']}💰\n\nВыберите действие:", 
                        admin_edit_keyboard(target_uid, "balance", users[target_uid]["balance"]))
        elif action == "house":
            edit_message(chat_id, message_id, f"👤 {target_name}\n🏠 Дом: {get_house_info(users[target_uid]['house_level'])['name']}\n\nВыберите действие:",
                        admin_edit_keyboard(target_uid, "house", users[target_uid]["house_level"]))
        elif action == "business":
            edit_message(chat_id, message_id, f"👤 {target_name}\n💼 Бизнесов: {users[target_uid]['businesses']}\n\nВыберите действие:",
                        admin_edit_keyboard(target_uid, "business", users[target_uid]["businesses"]))
        elif action == "farm":
            edit_message(chat_id, message_id, f"👤 {target_name}\n🌾 Ферм: {users[target_uid]['farms']}\n\nВыберите действие:",
                        admin_edit_keyboard(target_uid, "farm", users[target_uid]["farms"]))
    
    # Изменение значений
    elif data.startswith("admin_add_"):
        parts = data.split("_")
        field = parts[2]
        target_uid = int(parts[3])
        amount = int(parts[4])
        if field == "balance":
            users[target_uid]["balance"] += amount
        elif field == "house":
            new_level = min(5, users[target_uid]["house_level"] + 1)
            users[target_uid]["house_level"] = new_level
        elif field == "business":
            users[target_uid]["businesses"] += 1
        elif field == "farm":
            users[target_uid]["farms"] += 1
        save_users()
        edit_message(chat_id, message_id, f"✅ Изменено!\n{field}: {users[target_uid][field] if field != 'house' else get_house_info(users[target_uid]['house_level'])['name']}")
    
    elif data.startswith("admin_sub_"):
        parts = data.split("_")
        field = parts[2]
        target_uid = int(parts[3])
        amount = int(parts[4])
        if field == "balance":
            users[target_uid]["balance"] = max(0, users[target_uid]["balance"] - amount)
        elif field == "house":
            new_level = max(0, users[target_uid]["house_level"] - 1)
            users[target_uid]["house_level"] = new_level
        elif field == "business":
            users[target_uid]["businesses"] = max(0, users[target_uid]["businesses"] - 1)
        elif field == "farm":
            users[target_uid]["farms"] = max(0, users[target_uid]["farms"] - 1)
        save_users()
        edit_message(chat_id, message_id, f"✅ Изменено!")
    
    elif data.startswith("admin_back_select_"):
        field = data.split("_")[3]
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_selection_keyboard(field))

def main():
    global last_update_id
    load_users()
    print("🤖 Бот запущен!")
    
    while True:
        try:
            updates = get_updates(last_update_id + 1)
            if updates.get("ok"):
                for update in updates.get("result", []):
                    if "message" in update:
                        if update["message"].get("text"):
                            handle_message(update["message"])
                    if "callback_query" in update:
                        handle_callback(update["callback_query"])
                    last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
