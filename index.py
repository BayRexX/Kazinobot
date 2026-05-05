import random
import json
import os
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
DATA_FILE = "users_data.json"
users = {}
last_update_id = 0

# HTTP сервер для Render (чтобы был открытый порт)
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

# Запускаем HTTP сервер в отдельном потоке
threading.Thread(target=run_http_server, daemon=True).start()

def save_users():
    try:
        with open(DATA_FILE, 'w') as f:
            data = {}
            for uid, u in users.items():
                data[str(uid)] = u.copy()
                if data[str(uid)].get("last_daily"):
                    data[str(uid)]["last_daily"] = data[str(uid)]["last_daily"].isoformat()
            json.dump(data, f)
    except Exception as e:
        print(f"Save error: {e}")

def load_users():
    global users
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            for uid, u in data.items():
                if u.get("last_daily"):
                    u["last_daily"] = datetime.fromisoformat(u["last_daily"])
                users[int(uid)] = u
            print(f"Loaded {len(users)} users")
    except Exception as e:
        print(f"Load error: {e}")

def init_user(uid, name):
    if uid not in users:
        users[uid] = {
            "name": name,
            "balance": 1000,
            "businesses": 0,
            "farms": 0,
            "last_daily": None
        }
        save_users()

def send_message(chat_id, text):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data))
    except Exception as e:
        print(f"Send error: {e}")

def get_updates(offset):
    try:
        import urllib.request
        import json
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Get updates error: {e}")
        return {"ok": False, "result": []}

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    user_name = msg["from"].get("first_name", "User")
    text = msg.get("text", "")
    
    init_user(user_id, user_name)
    
    if text == "/start":
        send_message(chat_id,
            "🎰 КАЗИНО БОТ 🎰\n\n"
            "/balance - баланс\n"
            "/casino 100 - сыграть\n"
            "/allin - всё или ничего\n"
            "/business - бизнес (500💰)\n"
            "/farm - ферма (300💰)\n"
            "/collect - собрать доход\n"
            "/daily - бонус\n"
            "/give 100 - перевод\n"
            "/top - топ")
    
    elif text == "/balance":
        send_message(chat_id, f"💰 Баланс: {users[user_id]['balance']}💰")
    
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
            send_message(chat_id, f"❌ Нужно 500💰, у вас {users[user_id]['balance']}💰")
    
    elif text == "/farm":
        if users[user_id]["balance"] >= 300:
            users[user_id]["balance"] -= 300
            users[user_id]["farms"] += 1
            save_users()
            send_message(chat_id, f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
        else:
            send_message(chat_id, f"❌ Нужно 300💰, у вас {users[user_id]['balance']}💰")
    
    elif text == "/collect":
        total = users[user_id]["businesses"] * 50 + users[user_id]["farms"] * 30
        if total > 0:
            users[user_id]["balance"] += total
            save_users()
            send_message(chat_id, f"📦 Собрано {total}💰!\n💰 Баланс: {users[user_id]['balance']}💰")
        else:
            send_message(chat_id, "⏳ Нет бизнесов или ферм!")
    
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            send_message(chat_id, "❌ Бонус уже получен! Завтра.")
        else:
            users[user_id]["balance"] += 200
            users[user_id]["last_daily"] = today
            save_users()
            send_message(chat_id, f"🎁 БОНУС! +200💰\n💰 Баланс: {users[user_id]['balance']}💰")
    
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
                    last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
