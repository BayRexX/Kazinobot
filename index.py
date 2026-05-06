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
        print(f"Answer error: {e}")

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

# ========== АДМИН КЛАВИАТУРЫ ==========
def admin_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "💰 Баланс", "callback_data": "adm_bal"}],
            [{"text": "🏠 Дом", "callback_data": "adm_house"}],
            [{"text": "💼 Бизнес", "callback_data": "adm_biz"}],
            [{"text": "🌾 Ферма", "callback_data": "adm_farm"}],
            [{"text": "💾 Экспорт БД", "callback_data": "adm_export"}]
        ]
    }

def admin_user_list(page=0):
    keyboard = {"inline_keyboard": []}
    user_list = list(users.items())
    start = page * 10
    end = min(start + 10, len(user_list))
    
    for i in range(start, end):
        uid, u = user_list[i]
        keyboard["inline_keyboard"].append([
            {"text": f"👤 {u['name'][:20]}", "callback_data": f"adm_sel_{uid}"}
        ])
    
    nav = []
    if page > 0:
        nav.append({"text": "◀️ Назад", "callback_data": f"adm_page_{page-1}"})
    if end < len(user_list):
        nav.append({"text": "Вперед ▶️", "callback_data": f"adm_page_{page+1}"})
    if nav:
        keyboard["inline_keyboard"].append(nav)
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Главное меню", "callback_data": "adm_back"}])
    return keyboard

def admin_edit_menu(uid, field):
    u = users[uid]
    if field == "balance":
        text = f"👤 {u['name']}\n💰 Баланс: {u['balance']}💰"
        keyboard = {
            "inline_keyboard": [
                [{"text": "➕ +100", "callback_data": f"adm_add_bal_{uid}_100"}],
                [{"text": "➕ +1000", "callback_data": f"adm_add_bal_{uid}_1000"}],
                [{"text": "➖ -100", "callback_data": f"adm_sub_bal_{uid}_100"}],
                [{"text": "➖ -1000", "callback_data": f"adm_sub_bal_{uid}_1000"}],
                [{"text": "🔙 Назад", "callback_data": "adm_back_list"}]
            ]
        }
    elif field == "house":
        house = get_house_info(u['house_level'])
        text = f"👤 {u['name']}\n🏠 Дом: {house['name']} (ур.{u['house_level']})"
        keyboard = {
            "inline_keyboard": [
                [{"text": "⬆️ Повысить", "callback_data": f"adm_add_house_{uid}_1"}],
                [{"text": "⬇️ Понизить", "callback_data": f"adm_sub_house_{uid}_1"}],
                [{"text": "🔙 Назад", "callback_data": "adm_back_list"}]
            ]
        }
    elif field == "business":
        text = f"👤 {u['name']}\n💼 Бизнесов: {u['businesses']}"
        keyboard = {
            "inline_keyboard": [
                [{"text": "➕ +1", "callback_data": f"adm_add_biz_{uid}_1"}],
                [{"text": "➖ -1", "callback_data": f"adm_sub_biz_{uid}_1"}],
                [{"text": "🔙 Назад", "callback_data": "adm_back_list"}]
            ]
        }
    elif field == "farm":
        text = f"👤 {u['name']}\n🌾 Ферм: {u['farms']}"
        keyboard = {
            "inline_keyboard": [
                [{"text": "➕ +1", "callback_data": f"adm_add_farm_{uid}_1"}],
                [{"text": "➖ -1", "callback_data": f"adm_sub_farm_{uid}_1"}],
                [{"text": "🔙 Назад", "callback_data": "adm_back_list"}]
            ]
        }
    else:
        text = "Ошибка"
        keyboard = {}
    
    return text, keyboard

# ========== ПОКУПКА ДОМА КЛАВИАТУРА ==========
def house_buy_menu(uid):
    current_level = users[uid]['house_level']
    keyboard = {"inline_keyboard": []}
    
    for level in range(1, 6):
        house = get_house_info(level)
        if level == current_level + 1:
            keyboard["inline_keyboard"].append([
                {"text": f"🏠 {house['name']} - {house['price']}💰", "callback_data": f"buy_{level}"}
            ])
        elif level <= current_level:
            keyboard["inline_keyboard"].append([
                {"text": f"✅ {house['name']} (куплен)", "callback_data": "none"}
            ])
        else:
            keyboard["inline_keyboard"].append([
                {"text": f"🔒 {house['name']} (нужен уровень {level-1})", "callback_data": "none"}
            ])
    
    current_house = get_house_info(current_level)
    text = f"🏠 Ваш дом: {current_house['name']} (+{current_house['income']}💰/час)\n\nВыберите дом для покупки:"
    return text, keyboard

# ========== ОБРАБОТКА КОМАНД ==========
def handle_message(msg):
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    user_name = msg["from"].get("first_name", "User")
    text = msg.get("text", "")
    
    init_user(user_id, user_name)
    
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
    
    elif text == "/profile":
        show_profile(chat_id, user_id)
    
    elif text.startswith("/profile") and msg.get("reply_to_message"):
        target_id = msg["reply_to_message"]["from"]["id"]
        init_user(target_id, msg["reply_to_message"]["from"].get("first_name", "User"))
        show_profile(chat_id, target_id)
    
    elif text == "/balance":
        send_message(chat_id, f"💰 Баланс: {users[user_id]['balance']}💰")
    
    elif text == "/house":
        text, keyboard = house_buy_menu(user_id)
        send_message(chat_id, text, keyboard)
    
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
    
    elif text == "/business":
        if users[user_id]["balance"] >= 500:
            users[user_id]["balance"] -= 500
            users[user_id]["businesses"] += 1
            save_users()
            send_message(chat_id, f"✅ Бизнес куплен! -500💰\nДоход: 50💰/час")
        else:
            send_message(chat_id, f"❌ Нужно 500💰")
    
    elif text == "/farm":
        if users[user_id]["balance"] >= 300:
            users[user_id]["balance"] -= 300
            users[user_id]["farms"] += 1
            save_users()
            send_message(chat_id, f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
        else:
            send_message(chat_id, f"❌ Нужно 300💰")
    
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
    
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            send_message(chat_id, "❌ Бонус уже был сегодня!")
        else:
            bonus = 200
            users[user_id]["balance"] += bonus
            users[user_id]["last_daily"] = today
            save_users()
            send_message(chat_id, f"🎁 +{bonus}💰! Баланс: {users[user_id]['balance']}💰")
    
    elif text.startswith("/give "):
        if "reply_to_message" not in msg:
            send_message(chat_id, "❌ Ответьте на сообщение!")
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
                send_message(chat_id, f"❌ Не хватает!")
            else:
                init_user(receiver_id, receiver_name)
                users[user_id]["balance"] -= amount
                users[receiver_id]["balance"] += amount
                save_users()
                send_message(chat_id, f"✅ Переведено {amount}💰 {receiver_name}")
        except:
            send_message(chat_id, "💸 /give 100")
    
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
    
    elif text == "/admin":
        if user_id == ADMIN_ID:
            send_message(chat_id, "👑 АДМИН ПАНЕЛЬ", admin_main_menu())
        else:
            send_message(chat_id, "❌ Нет доступа!")

def show_profile(chat_id, user_id):
    u = users[user_id]
    house = get_house_info(u['house_level'])
    hourly_income = u["businesses"] * 50 + u["farms"] * 30 + house["income"]
    
    msg = (
        f"👤 <b>{u['name']}</b>\n\n"
        f"💰 Баланс: {u['balance']}💰\n"
        f"🏠 Дом: {house['name']} (+{house['income']}💰/ч)\n"
        f"💼 Бизнесов: {u['businesses']} (+{u['businesses']*50}💰/ч)\n"
        f"🌾 Ферм: {u['farms']} (+{u['farms']*30}💰/ч)\n"
        f"📊 Доход в час: {hourly_income}💰"
    )
    send_message(chat_id, msg)

# ========== ОБРАБОТКА CALLBACK ==========
def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    user_id = callback["from"]["id"]
    callback_id = callback["id"]
    data = callback["data"]
    
    if data == "none":
        answer_callback(callback_id, "Это действие недоступно", True)
        return
    
    # ПОКУПКА ДОМА (для обычных пользователей)
    if data.startswith("buy_"):
        level = int(data.split("_")[1])
        house = get_house_info(level)
        
        if users[user_id]["house_level"] + 1 == level:
            if users[user_id]["balance"] >= house["price"]:
                users[user_id]["balance"] -= house["price"]
                users[user_id]["house_level"] = level
                save_users()
                answer_callback(callback_id, f"✅ Куплен {house['name']}!", False)
                edit_message(chat_id, message_id, f"🏠 Поздравляем! Вы купили {house['name']}!\n💰 Остаток: {users[user_id]['balance']}💰")
            else:
                answer_callback(callback_id, f"❌ Нужно {house['price']}💰", True)
        else:
            answer_callback(callback_id, "❌ Покупай дома по порядку!", True)
        
        text, keyboard = house_buy_menu(user_id)
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    # АДМИН ПАНЕЛЬ
    if user_id != ADMIN_ID:
        answer_callback(callback_id, "❌ Нет доступа!", True)
        return
    
    # Главное меню админа
    if data == "adm_bal":
        admin_temp = {"action": "balance", "page": 0}
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_list(0))
    elif data == "adm_house":
        admin_temp = {"action": "house", "page": 0}
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_list(0))
    elif data == "adm_biz":
        admin_temp = {"action": "business", "page": 0}
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_list(0))
    elif data == "adm_farm":
        admin_temp = {"action": "farm", "page": 0}
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_list(0))
    elif data == "adm_export":
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                backup = f.read()
            if len(backup) > 4000:
                backup = backup[:4000] + "\n...(обрезано)"
            send_message(chat_id, f"💾 БД:\n<code>{backup}</code>")
            answer_callback(callback_id, "✅ Экспорт выполнен", False)
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка: {e}")
    elif data == "adm_back":
        edit_message(chat_id, message_id, "👑 АДМИН ПАНЕЛЬ", admin_main_menu())
    elif data == "adm_back_list":
        edit_message(chat_id, message_id, "👑 АДМИН ПАНЕЛЬ", admin_main_menu())
    
    # Пагинация
    elif data.startswith("adm_page_"):
        page = int(data.split("_")[2])
        edit_message(chat_id, message_id, "👑 Выберите пользователя:", admin_user_list(page))
    
    # Выбор пользователя
    elif data.startswith("adm_sel_"):
        target_uid = int(data.split("_")[2])
        # Определяем текущее действие из сообщения
        text = callback["message"]["text"]
        if "баланс" in text.lower():
            field = "balance"
        elif "дом" in text.lower():
            field = "house"
        elif "бизнес" in text.lower():
            field = "business"
        elif "ферм" in text.lower():
            field = "farm"
        else:
            field = "balance"
        
        edit_text, keyboard = admin_edit_menu(target_uid, field)
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    # Добавление/убавление
    elif data.startswith("adm_add_bal_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        amount = int(parts[4])
        users[target_uid]["balance"] += amount
        save_users()
        answer_callback(callback_id, f"✅ +{amount}💰", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "balance")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_sub_bal_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        amount = int(parts[4])
        users[target_uid]["balance"] = max(0, users[target_uid]["balance"] - amount)
        save_users()
        answer_callback(callback_id, f"✅ -{amount}💰", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "balance")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_add_house_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        users[target_uid]["house_level"] = min(5, users[target_uid]["house_level"] + 1)
        save_users()
        answer_callback(callback_id, "✅ Уровень дома повышен", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "house")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_sub_house_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        users[target_uid]["house_level"] = max(0, users[target_uid]["house_level"] - 1)
        save_users()
        answer_callback(callback_id, "✅ Уровень дома понижен", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "house")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_add_biz_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        users[target_uid]["businesses"] += 1
        save_users()
        answer_callback(callback_id, "✅ +1 бизнес", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "business")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_sub_biz_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        users[target_uid]["businesses"] = max(0, users[target_uid]["businesses"] - 1)
        save_users()
        answer_callback(callback_id, "✅ -1 бизнес", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "business")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_add_farm_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        users[target_uid]["farms"] += 1
        save_users()
        answer_callback(callback_id, "✅ +1 ферма", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "farm")
        edit_message(chat_id, message_id, edit_text, keyboard)
    
    elif data.startswith("adm_sub_farm_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        users[target_uid]["farms"] = max(0, users[target_uid]["farms"] - 1)
        save_users()
        answer_callback(callback_id, "✅ -1 ферма", False)
        edit_text, keyboard = admin_edit_menu(target_uid, "farm")
        edit_message(chat_id, message_id, edit_text, keyboard)

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
