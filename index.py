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
        req = urllib.request.Request(url, data=post_data, method="POST")
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Send error: {e}")

def answer_callback(callback_id, text, show_alert=False):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
        data = {"callback_query_id": callback_id, "text": text, "show_alert": show_alert}
        post_data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=post_data, method="POST")
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Answer callback error: {e}")

def edit_message(chat_id, message_id, text, reply_markup=None):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        post_data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=post_data, method="POST")
        urllib.request.urlopen(req)
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
            [{"text": "💾 Экспорт БД", "callback_data": "admin_export"}],
            [{"text": "📥 Импорт БД", "callback_data": "admin_import"}]
        ]
    }

def admin_user_list_keyboard(action):
    keyboard = {"inline_keyboard": []}
    count = 0
    for uid, u in users.items():
        if count >= 20:
            break
        keyboard["inline_keyboard"].append([
            {"text": f"👤 {u['name'][:20]}", "callback_data": f"adm_sel_{action}_{uid}"}
        ])
        count += 1
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "admin_back"}])
    return keyboard

def admin_edit_keyboard(uid, field):
    return {
        "inline_keyboard": [
            [{"text": "➕ +100", "callback_data": f"adm_add_{field}_{uid}_100"}],
            [{"text": "➕ +1000", "callback_data": f"adm_add_{field}_{uid}_1000"}],
            [{"text": "➖ -100", "callback_data": f"adm_sub_{field}_{uid}_100"}],
            [{"text": "➖ -1000", "callback_data": f"adm_sub_{field}_{uid}_1000"}],
            [{"text": "🔙 Назад к списку", "callback_data": f"adm_back_list_{field}"}],
            [{"text": "🔙 В главное меню", "callback_data": "admin_back"}]
        ]
    }

def house_buy_keyboard(current_level):
    keyboard = {"inline_keyboard": []}
    for level in range(1, 6):
        house = get_house_info(level)
        if level == current_level + 1:
            keyboard["inline_keyboard"].append([
                {"text": f"🏠 Купить {house['name']} - {house['price']}💰", "callback_data": f"buy_house_{level}"}
            ])
        elif level <= current_level:
            keyboard["inline_keyboard"].append([
                {"text": f"✅ {house['name']} (уже куплен)", "callback_data": "none"}
            ])
        else:
            keyboard["inline_keyboard"].append([
                {"text": f"🔒 {house['name']} (нужен дом уровнем ниже)", "callback_data": "none"}
            ])
    keyboard["inline_keyboard"].append([{"text": "🔙 Главное меню", "callback_data": "back_menu"}])
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
            "🏆 /top - топ\n"
            "👑 /admin - админ панель")
    
    # PROFILE
    elif text == "/profile":
        show_profile(chat_id, user_id)
    elif text.startswith("/profile") and msg.get("reply_to_message"):
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
            parts = text.split()
            if len(parts) != 2:
                send_message(chat_id, "🎲 /casino 100")
                return
            bet = int(parts[1])
            if bet <= 0:
                send_message(chat_id, "❌ Ставка должна быть больше 0!")
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
        except ValueError:
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
    
    # COLLECT
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
                send_message(chat_id, "⏳ У вас нет бизнесов, ферм и дома!")
    
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
                send_message(chat_id, "❌ Сумма должна быть больше 0!")
            elif users[user_id]["balance"] < amount:
                send_message(chat_id, f"❌ Не хватает! У вас {users[user_id]['balance']}💰")
            else:
                init_user(receiver_id, receiver_name)
                users[user_id]["balance"] -= amount
                users[receiver_id]["balance"] += amount
                save_users()
                send_message(chat_id, f"✅ Переведено {amount}💰 пользователю {receiver_name}")
                send_message(receiver_id, f"💰 {user_name} перевёл(а) вам {amount}💰!")
        except ValueError:
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
    elif text == "/admin":
        if user_id == ADMIN_ID:
            send_message(chat_id, "👑 АДМИН ПАНЕЛЬ 👑\nВыберите действие:", admin_main_keyboard())
        else:
            send_message(chat_id, "❌ У вас нет доступа к админ панели!")

def show_profile(chat_id, user_id):
    u = users[user_id]
    house = get_house_info(u['house_level'])
    hourly_income = u["businesses"] * 50 + u["farms"] * 30 + house["income"]
    
    if u["last_daily"] == datetime.now().date():
        daily_status = "✅ Получен сегодня"
    else:
        daily_status = "🎁 Доступен"
    
    msg = (
        f"👤 <b>{u['name']}</b>\n\n"
        f"💰 Баланс: {u['balance']}💰\n"
        f"🏠 Дом: {house['name']} (+{house['income']}💰/час)\n"
        f"💼 Бизнесов: {u['businesses']} (+{u['businesses']*50}💰/час)\n"
        f"🌾 Ферм: {u['farms']} (+{u['farms']*30}💰/час)\n"
        f"📊 Общий доход в час: {hourly_income}💰\n"
        f"🎁 Ежедневный бонус: {daily_status}"
    )
    send_message(chat_id, msg)

def show_house_menu(chat_id, user_id):
    current_level = users[user_id]['house_level']
    current_house = get_house_info(current_level)
    keyboard = house_buy_keyboard(current_level)
    msg = f"🏠 <b>Ваш дом:</b> {current_house['name']}\n💵 Доход: +{current_house['income']}💰/час\n\n<u>Доступные дома для покупки:</u>"
    send_message(chat_id, msg, keyboard)

# ========== ОБРАБОТКА CALLBACK ==========
def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    user_id = callback["from"]["id"]
    callback_id = callback["id"]
    data = callback["data"]
    
    # Пропускаем пустые кнопки
    if data == "none":
        answer_callback(callback_id, "Это действие недоступно", True)
        return
    
    # Покупка дома
    if data.startswith("buy_house_"):
        if user_id != ADMIN_ID:
            level = int(data.split("_")[2])
            house = get_house_info(level)
            if users[user_id]["house_level"] + 1 == level:
                if users[user_id]["balance"] >= house["price"]:
                    users[user_id]["balance"] -= house["price"]
                    users[user_id]["house_level"] = level
                    save_users()
                    answer_callback(callback_id, f"✅ Вы купили {house['name']}!", False)
                    edit_message(chat_id, message_id, f"🏠 Поздравляем! Вы купили {house['name']}!\n💰 Остаток: {users[user_id]['balance']}💰")
                else:
                    answer_callback(callback_id, f"❌ Не хватает! Нужно {house['price']}💰", True)
            else:
                answer_callback(callback_id, "❌ Нужно покупать дома по порядку!", True)
        show_house_menu(chat_id, user_id)
        return
    
    if data == "back_menu":
        send_message(chat_id, "🎰 Главное меню:\n/start - все команды")
        return
    
    # АДМИН ПАНЕЛЬ (только для админа)
    if user_id != ADMIN_ID:
        answer_callback(callback_id, "❌ У вас нет доступа!", True)
        return
    
    # Главное меню админа
    if data == "admin_balance":
        edit_message(chat_id, message_id, "👑 Выберите пользователя для изменения баланса:", admin_user_list_keyboard("balance"))
    elif data == "admin_house":
        edit_message(chat_id, message_id, "👑 Выберите пользователя для изменения дома:", admin_user_list_keyboard("house"))
    elif data == "admin_business":
        edit_message(chat_id, message_id, "👑 Выберите пользователя для изменения бизнесов:", admin_user_list_keyboard("business"))
    elif data == "admin_farm":
        edit_message(chat_id, message_id, "👑 Выберите пользователя для изменения ферм:", admin_user_list_keyboard("farm"))
    elif data == "admin_export":
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            if len(backup_data) > 4000:
                backup_data = backup_data[:4000] + "\n... (файл слишком большой)"
            send_message(chat_id, f"💾 <b>Экспорт базы данных</b>\n\n<code>{backup_data}</code>")
            answer_callback(callback_id, "✅ БД экспортирована", False)
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка экспорта: {e}")
    elif data == "admin_import":
        send_message(chat_id, "📥 Отправьте JSON файл с данными пользователей")
        answer_callback(callback_id, "Ожидаю файл с БД", False)
    elif data == "admin_back":
        edit_message(chat_id, message_id, "👑 АДМИН ПАНЕЛЬ 👑\nВыберите действие:", admin_main_keyboard())
    
    # Выбор пользователя
    elif data.startswith("adm_sel_"):
        parts = data.split("_")
        action = parts[2]
        target_uid = int(parts[3])
        target_name = users[target_uid]["name"]
        
        if action == "balance":
            edit_message(chat_id, message_id, 
                f"👤 <b>{target_name}</b>\n💰 Баланс: {users[target_uid]['balance']}💰\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "balance"))
        elif action == "house":
            house = get_house_info(users[target_uid]['house_level'])
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n🏠 Дом: {house['name']} (уровень {users[target_uid]['house_level']})\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "house"))
        elif action == "business":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n💼 Бизнесов: {users[target_uid]['businesses']}\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "business"))
        elif action == "farm":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n🌾 Ферм: {users[target_uid]['farms']}\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "farm"))
    
    # Изменение значений
    elif data.startswith("adm_add_"):
        parts = data.split("_")
        field = parts[2]
        target_uid = int(parts[3])
        amount = int(parts[4])
        
        if field == "balance":
            users[target_uid]["balance"] += amount
            save_users()
            answer_callback(callback_id, f"✅ +{amount}💰 пользователю {users[target_uid]['name']}", False)
        elif field == "house":
            new_level = min(5, users[target_uid]["house_level"] + 1)
            users[target_uid]["house_level"] = new_level
            save_users()
            answer_callback(callback_id, f"✅ Уровень дома повышен до {new_level}", False)
        elif field == "business":
            users[target_uid]["businesses"] += 1
            save_users()
            answer_callback(callback_id, f"✅ +1 бизнес (всего: {users[target_uid]['businesses']})", False)
        elif field == "farm":
            users[target_uid]["farms"] += 1
            save_users()
            answer_callback(callback_id, f"✅ +1 ферма (всего: {users[target_uid]['farms']})", False)
        
        # Обновляем сообщение
        target_name = users[target_uid]["name"]
        if field == "balance":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n💰 Баланс: {users[target_uid]['balance']}💰\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "balance"))
        elif field == "house":
            house = get_house_info(users[target_uid]['house_level'])
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n🏠 Дом: {house['name']} (уровень {users[target_uid]['house_level']})\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "house"))
        elif field == "business":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n💼 Бизнесов: {users[target_uid]['businesses']}\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "business"))
        elif field == "farm":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n🌾 Ферм: {users[target_uid]['farms']}\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "farm"))
    
    elif data.startswith("adm_sub_"):
        parts = data.split("_")
        field = parts[2]
        target_uid = int(parts[3])
        amount = int(parts[4])
        
        if field == "balance":
            users[target_uid]["balance"] = max(0, users[target_uid]["balance"] - amount)
            save_users()
            answer_callback(callback_id, f"✅ -{amount}💰 пользователю {users[target_uid]['name']}", False)
        elif field == "house":
            new_level = max(0, users[target_uid]["house_level"] - 1)
            users[target_uid]["house_level"] = new_level
            save_users()
            answer_callback(callback_id, f"✅ Уровень дома понижен до {new_level}", False)
        elif field == "business":
            users[target_uid]["businesses"] = max(0, users[target_uid]["businesses"] - 1)
            save_users()
            answer_callback(callback_id, f"✅ -1 бизнес (всего: {users[target_uid]['businesses']})", False)
        elif field == "farm":
            users[target_uid]["farms"] = max(0, users[target_uid]["farms"] - 1)
            save_users()
            answer_callback(callback_id, f"✅ -1 ферма (всего: {users[target_uid]['farms']})", False)
        
        # Обновляем сообщение
        target_name = users[target_uid]["name"]
        if field == "balance":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n💰 Баланс: {users[target_uid]['balance']}💰\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "balance"))
        elif field == "house":
            house = get_house_info(users[target_uid]['house_level'])
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n🏠 Дом: {house['name']} (уровень {users[target_uid]['house_level']})\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "house"))
        elif field == "business":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n💼 Бизнесов: {users[target_uid]['businesses']}\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "business"))
        elif field == "farm":
            edit_message(chat_id, message_id,
                f"👤 <b>{target_name}</b>\n🌾 Ферм: {users[target_uid]['farms']}\n\nВыберите действие:",
                admin_edit_keyboard(target_uid, "farm"))
    
    elif data.startswith("adm_back_list_"):
        field = data.split("_")[3]
        edit_message(chat_id, message_id, f"👑 Выберите пользователя для изменения {field}:", admin_user_list_keyboard(field))

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
                    if update["update_id"] > last_update_id:
                        last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
