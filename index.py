import random
import asyncio
import time
import json
import os
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

BOT_TOKEN = "8520721981:AAEoKN5DmuiDcL6YOjCP8vf0p3nbGcqHGyw"
DATA_FILE = "users_data.json"

# Функции для работы с файлом
def save_users():
    try:
        # Конвертируем datetime в строку для JSON
        data_to_save = {}
        for uid, user_data in users.items():
            data_to_save[uid] = user_data.copy()
            if data_to_save[uid]["last_daily"]:
                data_to_save[uid]["last_daily"] = data_to_save[uid]["last_daily"].isoformat()
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
            # Конвертируем обратно в datetime
            for uid, user_data in data.items():
                if user_data["last_daily"]:
                    user_data["last_daily"] = datetime.fromisoformat(user_data["last_daily"])
                users[int(uid)] = user_data
            print(f"✅ Загружено {len(users)} пользователей")
        else:
            print("📁 Новый файл данных создан")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")

# Хранилище данных
users = {}

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

async def check_level_up(user_id):
    user = users[user_id]
    need_exp = user['level'] * 100
    if user['exp'] >= need_exp:
        user['level'] += 1
        user['exp'] -= need_exp
        user['balance'] += user['level'] * 100
        save_users()
        await bot.send_message(user_id, f"🎉 ПОВЫШЕНИЕ ДО {user['level']} УРОВНЯ! +{user['level']*100} монет!")
        await check_level_up(user_id)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    await message.answer(
        "🎰 ДОБРО ПОЖАЛОВАТЬ В КАЗИНО 🎰\n\n"
        "💰 /баланс - проверка денег\n"
        "👤 /профиль - статистика\n"
        "🎲 /казино <число> - сделать ставку\n"
        "💀 /казиновсё - рискнуть всем\n"
        "💼 /бизнес - купить бизнес (500💰)\n"
        "🌾 /ферма - купить ферму (300💰)\n"
        "📦 /собрать - доход с бизнесов/ферм\n"
        "🎁 /ежедневный - бонус каждый день\n"
        "💸 /дать <сумма> - перевести (ответом)\n"
        "🏆 /топ - топ игроков\n"
        "⭐ /уровень - опыт и уровень\n"
        "🆘 /help - все команды"
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "📋 ВСЕ КОМАНДЫ:\n\n"
        "/баланс - баланс\n"
        "/профиль - статистика\n"
        "/казино <число> - ставка\n"
        "/казиновсё - всё или ничего\n"
        "/бизнес - купить бизнес (500💰)\n"
        "/ферма - купить ферму (300💰)\n"
        "/собрать - собрать доход\n"
        "/ежедневный - бонус раз в день\n"
        "/дать <сумма> - перевод (ответом)\n"
        "/топ - топ по деньгам\n"
        "/уровень - опыт и уровень\n"
        "/рейтинг - топ по уровню\n\n"
        "💾 Данные автоматически сохраняются!"
    )

@dp.message(Command("баланс"))
async def balance(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    await message.answer(f"💰 Ваш баланс: {users[uid]['balance']} монет")

@dp.message(Command("профиль"))
async def profile(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    u = users[uid]
    await message.answer(
        f"👤 {u['name']}\n"
        f"💰 Баланс: {u['balance']}\n"
        f"⭐ Уровень: {u['level']}\n"
        f"📊 Опыт: {u['exp']}/{u['level']*100}\n"
        f"🏢 Бизнесов: {u['businesses']}\n"
        f"🌾 Ферм: {u['farms']}"
    )

@dp.message(Command("уровень"))
async def level_cmd(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    u = users[uid]
    await message.answer(f"⭐ Уровень: {u['level']}\n📊 Опыт: {u['exp']}/{u['level']*100}")

@dp.message(Command("казино"))
async def casino(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("🎲 Использование: /казино <число>\nПример: /казино 100")
        return
    
    bet = int(args[1])
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0!")
        return
    
    if users[uid]["balance"] < bet:
        await message.answer(f"❌ Не хватает! У вас {users[uid]['balance']} монет")
        return
    
    if random.random() < 0.45:
        win = bet * 2
        users[uid]["balance"] += win
        users[uid]["exp"] += win // 10
        save_users()
        await check_level_up(uid)
        await message.answer(f"🎉 ПОБЕДА! +{win} монет\n💰 Баланс: {users[uid]['balance']}")
    else:
        users[uid]["balance"] -= bet
        save_users()
        await message.answer(f"😞 ПРОИГРЫШ! -{bet} монет\n💰 Баланс: {users[uid]['balance']}")

@dp.message(Command("казиновсё"))
async def casino_allin(message: Message):
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
        await check_level_up(uid)
        await message.answer(f"💀🔥 УДВОИЛИ! Баланс: {users[uid]['balance']} монет")
    else:
        users[uid]["balance"] = 0
        save_users()
        await message.answer(f"💀😭 ПРОИГРАЛИ ВСЁ! Баланс: 0 монет")

@dp.message(Command("бизнес"))
async def business(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    cost = 500
    if users[uid]["balance"] >= cost:
        users[uid]["balance"] -= cost
        users[uid]["businesses"] += 1
        save_users()
        await message.answer(f"✅ Бизнес куплен! -500💰\nДоход: 50💰 в час\nИспользуйте /собрать")
    else:
        await message.answer(f"❌ Нужно 500💰, у вас {users[uid]['balance']}")

@dp.message(Command("ферма"))
async def farm(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    cost = 300
    if users[uid]["balance"] >= cost:
        users[uid]["balance"] -= cost
        users[uid]["farms"] += 1
        save_users()
        await message.answer(f"✅ Ферма куплена! -300💰\nДоход: 30💰 в час")
    else:
        await message.answer(f"❌ Нужно 300💰, у вас {users[uid]['balance']}")

@dp.message(Command("собрать"))
async def collect(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    # Проверяем время последнего сбора (для честности)
    current_time = time.time()
    if 'last_collect' not in users[uid]:
        users[uid]['last_collect'] = current_time
    
    hours_passed = (current_time - users[uid]['last_collect']) // 3600
    if hours_passed < 1:
        await message.answer(f"⏳ Доход ещё не накоплен! Следующий сбор через {3600 - (current_time - users[uid]['last_collect']):.0f} сек")
        return
    
    total = users[uid]["businesses"] * 50 * hours_passed + users[uid]["farms"] * 30 * hours_passed
    if total > 0:
        users[uid]["balance"] += total
        users[uid]['last_collect'] = current_time
        save_users()
        await message.answer(f"📦 Собрано {total}💰 за {int(hours_passed)} час(ов)!\n💰 Баланс: {users[uid]['balance']}")
    else:
        await message.answer("⏳ У вас нет бизнесов или ферм! Купите: /бизнес или /ферма")

@dp.message(Command("ежедневный"))
async def daily(message: Message):
    uid = message.from_user.id
    init_user(uid, message.from_user.full_name)
    
    today = datetime.now().date()
    if users[uid]["last_daily"] == today:
        await message.answer("❌ Бонус уже получен! Завтра приходите.")
        return
    
    bonus = 200 + users[uid]["level"] * 50
    users[uid]["balance"] += bonus
    users[uid]["exp"] += 50
    users[uid]["last_daily"] = today
    save_users()
    await check_level_up(uid)
    await message.answer(f"🎁 ЕЖЕДНЕВНЫЙ БОНУС! +{bonus}💰 +50 опыта!\n💰 Баланс: {users[uid]['balance']}")

@dp.message(Command("дать"))
async def transfer(message: Message):
    sender_id = message.from_user.id
    init_user(sender_id, message.from_user.full_name)
    
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("💸 Использование: ответьте на сообщение и напишите /дать <сумма>")
        return
    
    amount = int(args[1])
    if amount <= 0:
        await message.answer("❌ Сумма должна быть положительной!")
        return
    
    if users[sender_id]["balance"] < amount:
        await message.answer(f"❌ Не хватает! У вас {users[sender_id]['balance']} монет")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение человека, которому хотите перевести!")
        return
    
    receiver = message.reply_to_message.from_user
    receiver_id = receiver.id
    
    init_user(receiver_id, receiver.full_name)
    
    users[sender_id]["balance"] -= amount
    users[receiver_id]["balance"] += amount
    save_users()
    
    await message.answer(f"✅ Переведено {amount}💰 пользователю {receiver.full_name}")
    await bot.send_message(receiver_id, f"💰 {message.from_user.full_name} перевёл вам {amount} монет!\nБаланс: {users[receiver_id]['balance']}")

@dp.message(Command("топ"))
async def top(message: Message):
    if not users:
        await message.answer("Нет игроков")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    result = "🏆 ТОП ПО БАЛАНСУ 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"{medal} {data['name']} — {data['balance']}💰\n"
    await message.answer(result)

@dp.message(Command("рейтинг"))
async def rating(message: Message):
    if not users:
        await message.answer("Нет игроков")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
    result = "⭐ ТОП ПО УРОВНЮ ⭐\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"{medal} {data['name']} — {data['level']} уровень\n"
    await message.answer(result)

# Автосохранение каждые 30 секунд
async def auto_save():
    while True:
        await asyncio.sleep(30)
        save_users()

# Функция для перезапуска бота при ошибке
async def run_bot():
    while True:
        try:
            print("🚀 Бот запускается...")
            load_users()  # Загружаем данные при старте
            asyncio.create_task(auto_save())  # Запускаем автосохранение
            await dp.start_polling(bot)
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            await asyncio.sleep(5)

async def main():
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())
