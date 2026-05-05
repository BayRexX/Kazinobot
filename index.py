import random
import json
import os
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
DATA_FILE = "users_data.json"
users = {}

def save_users():
    try:
        data_to_save = {}
        for uid, user_data in users.items():
            data_to_save[str(uid)] = user_data.copy()
            if data_to_save[str(uid)].get("last_daily"):
                data_to_save[str(uid)]["last_daily"] = data_to_save[str(uid)]["last_daily"].isoformat()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        print("✅ Данные сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def load_users():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for uid, user_data in data.items():
                if user_data.get("last_daily"):
                    user_data["last_daily"] = datetime.fromisoformat(user_data["last_daily"])
                users[int(uid)] = user_data
            print(f"✅ Загружено {len(users)} пользователей")
        else:
            print("📁 Новый файл данных")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")

def init_user(user_id, username):
    if user_id not in users:
        users[user_id] = {
            "name": username,
            "balance": 1000,
            "level": 1,
            "exp": 0,
            "businesses": 0,
            "farms": 0,
            "last_daily": None
        }
        save_users()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    init_user(message.from_user.id, message.from_user.full_name)
    await message.reply(
        "🎰 КАЗИНО БОТ 🎰\n\n"
        "💰 /balance - баланс\n"
        "👤 /profile - профиль\n"
        "🎲 /casino <число> - сделать ставку\n"
        "💀 /allin - рискнуть всем\n"
        "💼 /business - купить бизнес (500💰)\n"
        "🌾 /farm - купить ферму (300💰)\n"
        "📦 /collect - собрать доход\n"
        "🎁 /daily - ежедневный бонус\n"
        "💸 /give <сумма> - перевести (ответом)\n"
        "🏆 /top - топ игроков\n"
        "⭐ /level - уровень\n"
        "📊 /rating - топ по уровню"
    )

@dp.message_handler(commands=['balance'])
async def balance(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    await message.reply(f"💰 Баланс: {users[uid]['balance']} монет")

@dp.message_handler(commands=['profile'])
async def profile(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    u = users[uid]
    await message.reply(
        f"👤 {u['name']}\n"
        f"💰 {u['balance']}💰\n"
        f"⭐ Уровень {u['level']}\n"
        f"🏢 Бизнесов: {u['businesses']}\n"
        f"🌾 Ферм: {u['farms']}"
    )

@dp.message_handler(commands=['level'])
async def level_cmd(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    u = users[uid]
    need = u['level'] * 100
    await message.reply(f"⭐ Уровень: {u['level']}\n📊 Опыт: {u['exp']}/{need}")

@dp.message_handler(commands=['casino'])
async def casino(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    args = message.get_args().split()
    if len(args) != 1 or not args[0].isdigit():
        await message.reply("🎲 /casino <число>\nПример: /casino 100")
        return
    
    bet = int(args[0])
    if bet <= 0:
        await message.reply("❌ Ставка > 0!")
        return
    
    if users[uid]["balance"] < bet:
        await message.reply(f"❌ Не хватает! У вас {users[uid]['balance']}💰")
        return
    
    if random.random() < 0.45:
        win = bet * 2
        users[uid]["balance"] += win
        users[uid]["exp"] += win // 10
        save_users()
        await message.reply(f"🎉 ВЫИГРЫШ! +{win}💰\n💰 Баланс: {users[uid]['balance']}💰")
    else:
        users[uid]["balance"] -= bet
        save_users()
        await message.reply(f"😞 ПРОИГРЫШ! -{bet}💰\n💰 Баланс: {users[uid]['balance']}💰")

@dp.message_handler(commands=['allin'])
async def allin(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    bet = users[uid]["balance"]
    if bet <= 0:
        await message.reply("❌ Нечем рисковать!")
        return
    
    if random.random() < 0.4:
        users[uid]["balance"] *= 2
        users[uid]["exp"] += bet // 5
        save_users()
        await message.reply(f"💀🔥 УДВОИЛИ! Баланс: {users[uid]['balance']}💰")
    else:
        users[uid]["balance"] = 0
        save_users()
        await message.reply(f"💀😭 ПРОИГРАЛИ ВСЁ! Баланс: 0💰")

@dp.message_handler(commands=['business'])
async def business(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    if users[uid]["balance"] >= 500:
        users[uid]["balance"] -= 500
        users[uid]["businesses"] += 1
        save_users()
        await message.reply(f"✅ Бизнес куплен! -500💰\nДоход: 50💰/час")
    else:
        await message.reply(f"❌ Нужно 500💰, у вас {users[uid]['balance']}💰")

@dp.message_handler(commands=['farm'])
async def farm(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    if users[uid]["balance"] >= 300:
        users[uid]["balance"] -= 300
        users[uid]["farms"] += 1
        save_users()
        await message.reply(f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
    else:
        await message.reply(f"❌ Нужно 300💰, у вас {users[uid]['balance']}💰")

@dp.message_handler(commands=['collect'])
async def collect(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    total = users[uid]["businesses"] * 50 + users[uid]["farms"] * 30
    if total > 0:
        users[uid]["balance"] += total
        save_users()
        await message.reply(f"📦 Собрано {total}💰!\n💰 Баланс: {users[uid]['balance']}💰")
    else:
        await message.reply("⏳ Нет бизнесов или ферм! Купите /business или /farm")

@dp.message_handler(commands=['daily'])
async def daily(message: types.Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    today = datetime.now().date()
    if users[uid]["last_daily"] == today:
        await message.reply("❌ Бонус уже получен! Завтра.")
        return
    
    bonus = 200 + users[uid]["level"] * 50
    users[uid]["balance"] += bonus
    users[uid]["exp"] += 50
    users[uid]["last_daily"] = today
    save_users()
    await message.reply(f"🎁 БОНУС! +{bonus}💰 +50 опыта!\n💰 Баланс: {users[uid]['balance']}💰")

@dp.message_handler(commands=['give'])
async def give(message: types.Message):
    sender_id = message.from_user.id
    init_user(sender_id, message.from_user.full_name)
    
    args = message.get_args().split()
    if len(args) != 1 or not args[0].isdigit():
        await message.reply("💸 Ответьте на сообщение: /give 100")
        return
    
    amount = int(args[0])
    if amount <= 0 or users[sender_id]["balance"] < amount:
        await message.reply(f"❌ Не хватает! У вас {users[sender_id]['balance']}💰")
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение человека!")
        return
    
    receiver = message.reply_to_message.from_user
    init_user(receiver.id, receiver.full_name)
    
    users[sender_id]["balance"] -= amount
    users[receiver.id]["balance"] += amount
    save_users()
    
    await message.reply(f"✅ Переведено {amount}💰 {receiver.full_name}")

@dp.message_handler(commands=['top'])
async def top(message: types.Message):
    if not users:
        await message.reply("Нет игроков")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    result = "🏆 ТОП ПО БАЛАНСУ 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"{medal} {data['name']} — {data['balance']}💰\n"
    await message.reply(result)

@dp.message_handler(commands=['rating'])
async def rating(message: types.Message):
    if not users:
        await message.reply("Нет игроков")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
    result = "⭐ ТОП ПО УРОВНЮ ⭐\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"{medal} {data['name']} — {data['level']} уровень\n"
    await message.reply(result)

if __name__ == "__main__":
    load_users()
    print("🤖 Бот казино запущен!")
    executor.start_polling(dp, skip_updates=True)
