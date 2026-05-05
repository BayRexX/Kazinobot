import random
import json
import os
import asyncio
from datetime import datetime

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
DATA_FILE = "users_data.json"
users = {}

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
            "last_daily": None
        }
        save_users()

async def send_msg(chat_id, text):
    import aiohttp
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"chat_id": chat_id, "text": text})

async def handle_update(update):
    if "message" not in update:
        return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    user_name = msg["from"].get("first_name", "User")
    text = msg.get("text", "")
    
    init_user(user_id, user_name)
    
    if text == "/start":
        await send_msg(chat_id, 
            "🎰 КАЗИНО БОТ 🎰\n\n"
            "/balance - баланс\n"
            "/casino 100 - сыграть\n"
            "/allin - всё или ничего\n"
            "/business - бизнес (500💰)\n"
            "/farm - ферма (300💰)\n"
            "/collect - собрать доход\n"
            "/daily - бонус\n"
            "/give 100 - перевод (ответом)\n"
            "/top - топ игроков")
    
    elif text == "/balance":
        await send_msg(chat_id, f"💰 Баланс: {users[user_id]['balance']}💰")
    
    elif text.startswith("/casino "):
        try:
            bet = int(text.split()[1])
            if bet <= 0 or users[user_id]["balance"] < bet:
                await send_msg(chat_id, "❌ Не хватает денег!")
            else:
                if random.random() < 0.45:
                    win = bet * 2
                    users[user_id]["balance"] += win
                    save_users()
                    await send_msg(chat_id, f"🎉 ВЫИГРЫШ! +{win}💰\n💰 Баланс: {users[user_id]['balance']}💰")
                else:
                    users[user_id]["balance"] -= bet
                    save_users()
                    await send_msg(chat_id, f"😞 ПРОИГРЫШ! -{bet}💰\n💰 Баланс: {users[user_id]['balance']}💰")
        except:
            await send_msg(chat_id, "🎲 /casino 100")
    
    elif text == "/allin":
        bet = users[user_id]["balance"]
        if bet <= 0:
            await send_msg(chat_id, "❌ Нечем рисковать!")
        else:
            if random.random() < 0.4:
                users[user_id]["balance"] *= 2
                save_users()
                await send_msg(chat_id, f"💀🔥 УДВОИЛИ! Баланс: {users[user_id]['balance']}💰")
            else:
                users[user_id]["balance"] = 0
                save_users()
                await send_msg(chat_id, f"💀😭 ПРОИГРАЛИ ВСЁ! Баланс: 0💰")
    
    elif text == "/business":
        if users[user_id]["balance"] >= 500:
            users[user_id]["balance"] -= 500
            users[user_id]["businesses"] += 1
            save_users()
            await send_msg(chat_id, f"✅ Бизнес куплен! -500💰\nДоход: 50💰/час")
        else:
            await send_msg(chat_id, f"❌ Нужно 500💰, у вас {users[user_id]['balance']}💰")
    
    elif text == "/farm":
        if users[user_id]["balance"] >= 300:
            users[user_id]["balance"] -= 300
            users[user_id]["farms"] += 1
            save_users()
            await send_msg(chat_id, f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
        else:
            await send_msg(chat_id, f"❌ Нужно 300💰, у вас {users[user_id]['balance']}💰")
    
    elif text == "/collect":
        total = users[user_id]["businesses"] * 50 + users[user_id]["farms"] * 30
        if total > 0:
            users[user_id]["balance"] += total
            save_users()
            await send_msg(chat_id, f"📦 Собрано {total}💰!\n💰 Баланс: {users[user_id]['balance']}💰")
        else:
            await send_msg(chat_id, "⏳ Нет бизнесов или ферм!")
    
    elif text == "/daily":
        today = datetime.now().date()
        if users[user_id]["last_daily"] == today:
            await send_msg(chat_id, "❌ Бонус уже получен! Завтра.")
        else:
            bonus = 200
            users[user_id]["balance"] += bonus
            users[user_id]["last_daily"] = today
            save_users()
            await send_msg(chat_id, f"🎁 ЕЖЕДНЕВНЫЙ БОНУС! +{bonus}💰\n💰 Баланс: {users[user_id]['balance']}💰")
    
    elif text.startswith("/give "):
        if not msg.get("reply_to_message"):
            await send_msg(chat_id, "❌ Ответьте на сообщение человека!")
            return
        
        try:
            amount = int(text.split()[1])
            receiver_id = msg["reply_to_message"]["from"]["id"]
            receiver_name = msg["reply_to_message"]["from"].get("first_name", "User")
            
            if amount <= 0 or users[user_id]["balance"] < amount:
                await send_msg(chat_id, "❌ Не хватает денег!")
            else:
                init_user(receiver_id, receiver_name)
                users[user_id]["balance"] -= amount
                users[receiver_id]["balance"] += amount
                save_users()
                await send_msg(chat_id, f"✅ Переведено {amount}💰 {receiver_name}")
        except:
            await send_msg(chat_id, "💸 /give 100 (ответом на сообщение)")
    
    elif text == "/top":
        if not users:
            await send_msg(chat_id, "Нет игроков")
        else:
            sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
            result = "🏆 ТОП ПО БАЛАНСУ 🏆\n\n"
            for i, (uid, data) in enumerate(sorted_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                result += f"{medal} {data['name']} — {data['balance']}💰\n"
            await send_msg(chat_id, result)

async def main():
    load_users()
    print("🤖 Бот запущен!")
    
    import aiohttp
    offset = 0
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
                async with session.get(url, params={"offset": offset, "timeout": 30}) as resp:
                    data = await resp.json()
                    
                    if data.get("ok"):
                        for update in data.get("result", []):
                            await handle_update(update)
                            offset = update["update_id"] + 1
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
