import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# Настройки базы данных
MONGO_URI = "mongodb://localhost:27017"

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = MongoClient(MONGO_URI)
db = client["task_manager"]
tasks_collection = db["tasks"]

# Команда /start
@dp.message(lambda message: message.text == "/start")
async def start_command(message: Message):
    await message.answer("Привет! Я бот-планировщик. Используй /add_task, /tasks, /edit_task, /delete_task")

# Добавление задачи
@dp.message(lambda message: message.text.startswith("/add_task"))
async def add_task(message: Message):
    try:
        parts = message.text.split("|", 2)
        if len(parts) != 3:
            raise ValueError("Неправильное количество частей после split")

        _, task_text, deadline = map(str.strip, parts)
        deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M")

        task = {
            "user_id": message.from_user.id,
            "text": task_text,
            "deadline": deadline,
            "completed": False
        }

        tasks_collection.insert_one(task)
        await message.answer(f"✅ Задача добавлена!\n📌 {task_text}\n🕒 Дедлайн: {deadline}")
    except ValueError as e:
        await message.answer("⚠ Ошибка! Используй формат: /add_task | текст задачи | ГГГГ-ММ-ДД ЧЧ:ММ")
    except Exception as e:
        await message.answer("⚠ Произошла ошибка. Проверь формат ввода.")
        print(f"[Ошибка Exception] {e}")

# Вывод списка задач
@dp.message(lambda message: message.text == "/tasks")
async def list_tasks(message: Message):
    tasks = list(tasks_collection.find({"user_id": message.from_user.id}))
    if not tasks:
        await message.answer("📭 У вас нет задач.")
        return
    
    response = "📋 Ваши задачи:\n"
    now = datetime.now()
    for task in tasks:
        remaining = (task['deadline'] - now).total_seconds()
        status = "✅" if task.get("completed") else "❌"
        time_left = f"⏳ Осталось: {int(remaining // 3600)} ч {int((remaining % 3600) // 60)} м" if remaining > 0 else "🔥 Просрочено!"
        response += f"{status} {task['text']} ({time_left})\n"
    
    await message.answer(response)

# Удаление задачи
@dp.message(lambda message: message.text.startswith("/delete_task"))
async def delete_task(message: Message):
    try:
        _, task_text = message.text.split(" ", 1)
        result = tasks_collection.delete_one({"user_id": message.from_user.id, "text": task_text.strip()})
        if result.deleted_count:
            await message.answer("🗑 Задача удалена.")
        else:
            await message.answer("⚠ Задача не найдена.")
    except:
        await message.answer("⚠ Ошибка! Используй формат: /delete_task текст задачи")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')