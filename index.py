import random
import json
import os
import time
import asyncio
from datetime import datetime
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import threading

# Flask для health check
flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Bot is running!", 200

@flask_app.route('/ping')
def ping():
    return "pong", 200

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
            print("📁 Новый файл данных будет создан")
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
            "last_daily": None,
            "last_collect": time.time()
        }
        save_users()

async def check_level_up(user_id, bot):
    user = users[user_id]
    need_exp = user['level'] * 100
    if user['exp'] >= need_exp:
        user['level'] += 1
        user['exp'] -= need_exp
        user['balance'] += user['level'] * 100
        save_users()
        await bot.send_message(user_id, f"🎉 ПОВЫШЕНИЕ УРОВНЯ! Теперь {user['level']} уровень! +{user['level']*100} монет!")
        await check_level_up(user_id, bot)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    init_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        "🎰 ДОБРО ПОЖАЛОВАТЬ В КАЗИНО 🎰\n\n"
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
        "⭐ /level - уровень и опыт\n"
        "📊 /rating - топ по уровню\n"
        "🆘 /help - все команды"
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "📋 ВСЕ КОМАНДЫ 📋\n\n"
        "/balance - показать баланс\n"
        "/profile - статистика\n"
        "/casino <число> - сыграть\n"
        "/allin - рискнуть всем\n"
        "/business - купить бизнес (500💰)\n"
        "/farm - купить ферму (300💰)\n"
        "/collect - собрать доход\n"
        "/daily - бонус каждый день\n"
        "/give <сумма> - перевести (ответом)\n"
        "/top - топ 10 по деньгам\n"
        "/level - уровень и опыт\n"
        "/rating - топ 10 по уровню"
    )

@dp.message(Command("balance"))
async def balance(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    await message.answer(f"💰 Ваш баланс: {users[uid]['balance']} монет")

@dp.message(Command("profile"))
async def profile(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    u = users[uid]
    await message.answer(
        f"👤 {u['name']}\n"
        f"💰 Баланс: {u['balance']}💰\n"
        f"⭐ Уровень: {u['level']}\n"
        f"📊 Опыт: {u['exp']}/{u['level']*100}\n"
        f"🏢 Бизнесов: {u['businesses']}\n"
        f"🌾 Ферм: {u['farms']}"
    )

@dp.message(Command("level"))
async def level_cmd(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    u = users[uid]
    need = u['level'] * 100
    await message.answer(f"⭐ Уровень: {u['level']}\n📊 Опыт: {u['exp']}/{need}\n📈 Осталось: {need - u['exp']} опыта")

@dp.message(Command("casino"))
async def casino(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("🎲 Использование: /casino <число>\nПример: /casino 100")
        return
    
    bet = int(args[1])
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0!")
        return
    
    if users[uid]["balance"] < bet:
        await message.answer(f"❌ Не хватает! У вас {users[uid]['balance']}💰")
        return
    
    if random.random() < 0.45:
        win = bet * 2
        users[uid]["balance"] += win
        users[uid]["exp"] += win // 10
        save_users()
        await check_level_up(uid, bot)
        await message.answer(f"🎉 ВЫИГРЫШ! +{win}💰\n💰 Баланс: {users[uid]['balance']}💰")
    else:
        users[uid]["balance"] -= bet
        save_users()
        await message.answer(f"😞 ПРОИГРЫШ! -{bet}💰\n💰 Баланс: {users[uid]['balance']}💰")

@dp.message(Command("allin"))
async def allin(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    bet = users[uid]["balance"]
    if bet <= 0:
        await message.answer("❌ Нечем рисковать!")
        return
    
    if random.random() < 0.4:
        users[uid]["balance"] *= 2
        users[uid]["exp"] += bet // 5
        save_users()
        await check_level_up(uid, bot)
        await message.answer(f"💀🔥 УДВОИЛИ! Баланс: {users[uid]['balance']}💰")
    else:
        users[uid]["balance"] = 0
        save_users()
        await message.answer(f"💀😭 ПРОИГРАЛИ ВСЁ! Баланс: 0💰")

@dp.message(Command("business"))
async def business(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    cost = 500
    if users[uid]["balance"] >= cost:
        users[uid]["balance"] -= cost
        users[uid]["businesses"] += 1
        save_users()
        await message.answer(f"✅ Бизнес куплен! -500💰\nДоход: 50💰/час\nИспользуйте /collect для сбора")
    else:
        await message.answer(f"❌ Нужно 500💰, у вас {users[uid]['balance']}💰")

@dp.message(Command("farm"))
async def farm(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    cost = 300
    if users[uid]["balance"] >= cost:
        users[uid]["balance"] -= cost
        users[uid]["farms"] += 1
        save_users()
        await message.answer(f"✅ Ферма куплена! -300💰\nДоход: 30💰/час")
    else:
        await message.answer(f"❌ Нужно 300💰, у вас {users[uid]['balance']}💰")

@dp.message(Command("collect"))
async def collect(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    now = time.time()
    
    business_income = users[uid]["businesses"] * 50
    farm_income = users[uid]["farms"] * 30
    total_per_hour = business_income + farm_income
    
    if total_per_hour > 0:
        if 'last_collect' not in users[uid]:
            users[uid]['last_collect'] = now
        
        hours = (now - users[uid]['last_collect']) // 3600
        
        if hours >= 1:
            total = int(total_per_hour * hours)
            users[uid]["balance"] += total
            users[uid]['last_collect'] = now
            save_users()
            await message.answer(f"📦 Собрано {total}💰 за {int(hours)} час(ов)!\n💰 Баланс: {users[uid]['balance']}💰")
        else:
            remaining = 3600 - (now - users[uid]['last_collect'])
            minutes = int(remaining // 60)
            await message.answer(f"⏳ До следующего сбора: {minutes} минут")
    else:
        await message.answer("⏳ У вас нет бизнесов или ферм! Купите: /business или /farm")

@dp.message(Command("daily"))
async def daily(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    today = datetime.now().date()
    if users[uid]["last_daily"] == today:
        await message.answer("❌ Бонус уже получен! Приходите завтра.")
        return
    
    bonus = 200 + users[uid]["level"] * 50
    users[uid]["balance"] += bonus
    users[uid]["exp"] += 50
    users[uid]["last_daily"] = today
    save_users()
    await check_level_up(uid, bot)
    await message.answer(f"🎁 ЕЖЕДНЕВНЫЙ БОНУС! +{bonus}💰 +50 опыта!\n💰 Баланс: {users[uid]['balance']}💰")

@dp.message(Command("give"))
async def give(message: Message):
    sender_id = message.from_user.id
    init_user(sender_id, message.from_user.full_name)
    
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("💸 Использование: ответьте на сообщение и напишите /give <сумма>\nПример: /give 100")
        return
    
    amount = int(args[1])
    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0!")
        return
    
    if users[sender_id]["balance"] < amount:
        await message.answer(f"❌ Не хватает! У вас {users[sender_id]['balance']}💰")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение человека, которому хотите перевести!")
        return
    
    receiver = message.reply_to_message.from_user
    init_user(receiver.id, receiver.full_name)
    
    users[sender_id]["balance"] -= amount
    users[receiver.id]["balance"] += amount
    save_users()
    
    await message.answer(f"✅ Переведено {amount}💰 пользователю {receiver.full_name}")
    await bot.send_message(receiver.id, f"💰 {message.from_user.full_name} перевёл(а) вам {amount}💰\nВаш баланс: {users[receiver.id]['balance']}💰")

@dp.message(Command("top"))
async def top(message: Message):
    if not users:
        await message.answer("Нет игроков")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    result = "🏆 ТОП ПО БАЛАНСУ 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"{medal} {data['name']} — {data['balance']}💰 (Ур.{data['level']})\n"
    await message.answer(result)

@dp.message(Command("rating"))
async def rating(message: Message):
    if not users:
        await message.answer("Нет игроков")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
    result = "⭐ ТОП ПО УРОВНЮ ⭐\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"{medal} {data['name']} — {data['level']} уровень (опыта: {data['exp']})\n"
    await message.answer(result)

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080, debug=False)

async def main():
    load_users()
    print("🤖 Бот казино запущен!")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
