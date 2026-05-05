import random
import json
import os
import urllib.request
import urllib.parse
import threading
import time
from datetime import datetime

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
DATA_FILE = "users_data.json"
users = {}
last_update_id = 0

def save_users():
    try:
        with open(DATA_FILE, 'w') as f:
            data = {}
            for uid, u in users.items():
                data[str(uid)] = u.copy()
                if data[str(uid)].get("last_daily"):
                    data[str(uid)]["last_daily"] = data[str(uid)]["last_daily"].isoformat()
            json.dump(data, f)
        print("✅ Saved")
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
            print(f"✅ Loaded {len(users)} users")
    except Exception as e:
        print(f"Load error: {e}")

def init_user(uid, name):
    if uid not in users:
        users[uid] = {
            "name": name,
            "balance": 1000,
            "businesses": 0,
            "farms": 0,
            "last_daily": None,
            "level": 1,
            "exp": 0
        }
        save_users()

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Send error: {e}")

def get_updates(offset):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Get updates error: {e}")
        return {"ok": False, "result": []}

def handle_message(msg):
    global users
    
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
            "🎲 /casino 100 - сыграть\n"
            "💀 /allin - всё или ничего\n"
            "💼 /business - бизнес (500💰)\n"
            "🌾 /farm - ферма (300💰)\n"
            "📦 /collect - собрать доход\n"
            "🎁 /daily - бонус\n"
            "💸 /give 100 - перевод\n"
            "🏆 /top - топ\n"
            "⭐ /level - уровень")
    
    # BALANCE
    elif text == "/balance":
        send_message(chat_id, f"💰 Баланс: {users[user_id]['balance']}💰")
    
    # PROFILE
    elif text == "/profile":
        u = users[user_id]
        send_message(chat_id,
            f"👤 {u['name']}\n"
            f"💰 {u['balance']}💰\n"
            f"⭐ Уровень {u['level']}\n"
            f"🏢 Бизнесов: {u['businesses']}\n"
            f"🌾 Ферм: {u['farms']}")
    
    # LEVEL
    elif text == "/level":
        u = users[user_id]
        need = u['level'] * 100
        send_message(chat_id, f"⭐ Уровень: {u['level']}\n📊 Опыт: {u['exp']}/{need}")
    
    # CASINO
    elif text.startswith("/casino "):
        try:
            bet = int(text.split()[1])
            if bet <= 0:
                send_message(chat_id, "❌ Ставка должна быть больше 0!")
            elif users[user_id]["balance"] < bet:
                send_message(chat_id, f"❌ Не хватает! У вас {users[user_id]['balance']}💰")
            else:
                if random.random() < 0.45:
                    win = bet * 2
                    users[user_id]["balance"] += win
                    users[user_id]["exp"] += win // 10
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
                users[user_id]["exp"] += bet // 5
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
        total = users[user_id]["businesses"] * 50 + users[user_id]["farms"] * 30
        if total > 0:
            users[user_id]["balance"] += total
            save_users()
            send_message(chat_id, f"📦 Собрано {total}💰!\n💰 Баланс: {users[user_id]['balance']}💰")
        else:
            send_message(chat_id, "⏳ Нет бизнесов или ферм!")
    
    # DAILY
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            send_message(chat_id, "❌ Бонус уже получен! Завтра.")
        else:
            bonus = 200 + users[user_id]["level"] * 50
            users[user_id]["balance"] += bonus
            users[user_id]["exp"] += 50
            users[user_id]["last_daily"] = today
            save_users()
            send_message(chat_id, f"🎁 БОНУС! +{bonus}💰 +50 опыта!\n💰 Баланс: {users[user_id]['balance']}💰")
    
    # GIVE
    elif text.startswith("/give "):
        if "reply_to_message" not in msg:
            send_message(chat_id, "❌ Ответьте на сообщение человека!")
            return
        
        try:
            amount = int(text.split()[1])
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
                    last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
