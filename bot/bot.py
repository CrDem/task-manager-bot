import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from celery import Celery
from datetime import datetime, timedelta
import asyncio
import nest_asyncio
from celery.result import AsyncResult
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
celery_app =Celery('bot', broker='amqp://guest:guest@localhost:5672//')


# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = "mongodb://localhost:27017"

# Настройки бота и базы данных
bot = Bot(token=TOKEN)
dp = Dispatcher()
client = MongoClient(MONGO_URI)
db = client["task_manager"]
tasks_collection = db["tasks"]
user_states_collection = db["user_states"]
nest_asyncio.apply()


async def send_async_notification(user_id, text):
    """Асинхронная функция для отправки уведомлений"""
    try:
        await bot.send_message(chat_id=user_id, text=f"⏰ Напоминание: {text}")
        logger.info(f"Уведомление отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления для пользователя {user_id}: {e}")


@celery_app.task(name='bot.send_notification')
def send_notification(user_id, text):
    """Celery-задача, запускающая асинхронную отправку уведомлений"""
    try:
        asyncio.run(send_async_notification(user_id, text))
    except Exception as e:
        logger.error(f"Ошибка в send_notification: {e}")




def schedule_notification(user_id, text, deadline):
    """Запланировать уведомление за час до дедлайна"""
    notify_time = deadline - timedelta(hours=1)
    delay = (notify_time - datetime.now()).total_seconds()

    if delay > 0:
        task = send_notification.apply_async((user_id, text), countdown=delay)
        return task.id  # Сохраняем ID задачи в БД
    return None

def revoke_notification(task_id):
    """
    Отменяет задачу по её ID.
    """
    celery_app.control.revoke(task_id, terminate=True)
    logger.info(f"Задача {task_id} удалена")
from bson import ObjectId




# Главное меню
async def main_menu(chat_id):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Показать задачи", callback_data="show_tasks")],
        [InlineKeyboardButton(text="✏ Управление задачами", callback_data="manage_tasks")]
    ])
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Очистка чата
async def clear_chat(message: Message, skipThisMessage: 1):
    chat_id = message.chat.id
    try:
        for i in range(message.message_id - skipThisMessage, message.message_id - 100, -1):  # Удаляем последние 100 сообщений
            try:
                await bot.delete_message(chat_id, i)
            except Exception:
                break
    except Exception as e:
        logging.warning(f"Ошибка при очистке чата: {e}")

# Очистка состояния пользователя
async def clear_state(user_id: id):
    if user_states_collection.find_one({"user_id": user_id}):
        user_states_collection.delete_one({"user_id": user_id})

# Обработчик команды /start
@dp.message(F.text == "/start")
async def start_command(message: Message):
    await clear_state(message.from_user.id)
    await clear_chat(message, 0)
    await main_menu(message.chat.id)

# Показ задач
@dp.callback_query(F.data == "show_tasks")
async def show_tasks(callback: CallbackQuery):
    await clear_state(callback.from_user.id)
    await clear_chat(callback.message, 0)
    tasks = list(tasks_collection.find({"user_id": callback.from_user.id}))
    if not tasks:
        await bot.send_message(callback.message.chat.id, "📭 У вас нет задач.")
    else:
        response = "📋 Ваши задачи:\n"
        now = datetime.now()
        for task in tasks:
            remaining = (task['deadline'] - now).total_seconds()
            status = "✅" if task.get("completed") else "❌"
            time_left = f"⏳ Осталось: {int(remaining // 3600)} ч {int((remaining % 3600) // 60)} м" if remaining > 0 else "🔥 Просрочено!"
            response += f"{status} {task['text']} ({time_left})\n"
        
        await bot.send_message(callback.message.chat.id, response)
    await main_menu(callback.message.chat.id)

# Управление задачами
@dp.callback_query(F.data == "manage_tasks")
async def manage_tasks(callback: CallbackQuery):
    await clear_chat(callback.message, 0)
    tasks = list(tasks_collection.find({"user_id": callback.from_user.id}))
    task_buttons = [[InlineKeyboardButton(text=task["text"], callback_data=f"edit_{task['_id']}")] for task in tasks]
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
        *task_buttons,
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_tasks")]
    ])
    
    await bot.send_message(callback.message.chat.id, "Выберите действие:", reply_markup=markup)

# Добавление задачи - Шаг 1: Ввод дедлайна
@dp.callback_query(F.data == "add_task")
async def add_task(callback: CallbackQuery):
    user_states_collection.update_one({"user_id": callback.from_user.id}, {"$set": {"state": "waiting_for_deadline"}}, upsert=True)
    await bot.send_message(callback.message.chat.id, "Введите дедлайн задачи в формате ГГГГ-ММ-ДД ЧЧ:ММ:")

# Ввод текста от пользователя
@dp.message()
async def process_message(message: Message):
    user_id = message.from_user.id
    user_state = user_states_collection.find_one({"user_id": user_id})

    if not user_state:
        await main_menu(message.chat.id)
        return

    state = user_state.get("state")

    if state == "waiting_for_deadline":
        try:
            deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            if deadline < datetime.now():
                await message.answer("⚠ Дедлайн не может быть в прошлом. Попробуйте снова.")
                return
            user_states_collection.update_one({"user_id": user_id},
                                              {"$set": {"state": "waiting_for_text", "deadline": deadline}},
                                              upsert=True)
            await message.answer("Теперь введите текст задачи:")
        except ValueError:
            await message.answer("⚠ Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ")

    elif state == "waiting_for_text":
        task = {
            "user_id": user_id,
            "text": message.text,
            "deadline": user_state["deadline"],
            "completed": False
        }
        tasks_collection.insert_one(task)
        task_id = task["_id"]

        # Запланировать уведомление за час до дедлайна
        celery_task_id = schedule_notification(user_id, message.text, user_state["deadline"])

        # Обновляем запись в базе данных, добавляя celery_task_id
        tasks_collection.update_one(
            {"_id": task_id},
            {"$set": {"celery_task_id": celery_task_id}}
        )

        await message.answer("✅ Задача добавлена и уведомление установлено!")
        user_states_collection.delete_one({"user_id": user_id})

    elif state == "waiting_for_new_text":
        task_id = user_state.get("task_changing_id")
        tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"text": message.text}})
        await message.answer("✅ Текст задачи был успешно изменен!")
        user_states_collection.delete_one({"user_id": user_id})
        await clear_chat(message, 0)
        await main_menu(message.chat.id)

    elif state == "waiting_for_new_deadline":
        task_id = user_state.get("task_changing_id")
        try:
            new_deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            if new_deadline < datetime.now():
                await message.answer("⚠ Новый дедлайн не может быть в прошлом. Попробуйте снова.")
                return
            tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"deadline": new_deadline}})
            # Находим текущую задачу в базе данных
            task_record = tasks_collection.find_one({"_id": ObjectId(task_id)})
            # Отменяем старую задачу Celery
            old_celery_task_id = task_record.get("celery_task_id")
            revoke_notification(old_celery_task_id)

            # Перезапланировать уведомление для новой даты
            new_celery_task_id = schedule_notification(user_id, task_record["text"], new_deadline)

            # Обновляем запись в базе данных
            tasks_collection.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "deadline": new_deadline,
                        "celery_task_id": new_celery_task_id
                    }
                }
            )
            await message.answer("✅ Дедлайн задачи был успешно изменен!")
            user_states_collection.delete_one({"user_id": user_id})
            await clear_chat(message, 0)
            await main_menu(message.chat.id)
        except ValueError:
            await message.answer("⚠ Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ.")



# Управление конкретной задачей
@dp.callback_query(F.data.startswith("edit_"))
async def edit_task(callback: CallbackQuery):
    task_id = callback.data.split("_")[1]
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        await callback.answer("⚠ Задача не найдена.", show_alert=True)
        return
    
    await clear_state(callback.from_user.id)
    await clear_chat(callback.message, 1)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить выполненной", callback_data=f"complete_{task_id}")],
        [InlineKeyboardButton(text="✏ Изменить текст", callback_data=f"change_text_{task_id}")],
        [InlineKeyboardButton(text="⏳ Изменить время", callback_data=f"change_time_{task_id}")],
        [InlineKeyboardButton(text="🗑 Удалить задачу", callback_data=f"remove_task_{task_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_tasks")]
    ])
    
    await bot.send_message(callback.message.chat.id, f"📌 {task['text']}\n🕒 Дедлайн: {task['deadline']}", reply_markup=markup)

# Отметка задачи выполненной
@dp.callback_query(F.data.startswith("complete_"))
async def complete_task(callback: CallbackQuery):
    task_id = callback.data.split("_")[1]
    tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": True}})
    await callback.answer("✅ Задача отмечена как выполненная.", show_alert=True)
    await manage_tasks(callback)

# Удаление задачи
@dp.callback_query(F.data.startswith("remove_task_"))
async def remove_task(callback: CallbackQuery):
    task_id = callback.data.split("_")[2]
    task_record = tasks_collection.find_one({"_id": ObjectId(task_id)})
    celery_task_id = task_record.get("celery_task_id")
    revoke_notification(celery_task_id)
    tasks_collection.delete_one({"_id": ObjectId(task_id)})
    await callback.answer("🗑 Задача удалена.", show_alert=True)
    await manage_tasks(callback)

# Изменение текста задачи
@dp.callback_query(F.data.startswith("change_text_"))
async def change_text(callback: CallbackQuery):
    task_id = callback.data.split("_")[2]  # Извлекаем task_id
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        await callback.answer("⚠ Задача не найдена.", show_alert=True)
        return

    user_states_collection.update_one({"user_id": callback.from_user.id}, {"$set": {"state": "waiting_for_new_text", "task_changing_id": task_id}}, upsert=True)
    await callback.message.edit_text(f"Вы хотите изменить текст задачи: {task['text']}. Пожалуйста, введите новый текст задачи:")

# Изменение дедлайна задачи
@dp.callback_query(F.data.startswith("change_time_"))
async def change_time(callback: CallbackQuery):
    task_id = callback.data.split("_")[2]  # Извлекаем task_id
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        await callback.answer("⚠ Задача не найдена.", show_alert=True)
        return

    user_states_collection.update_one({"user_id": callback.from_user.id}, {"$set": {"state": "waiting_for_new_deadline", "task_changing_id": task_id}}, upsert=True)
    await callback.message.edit_text(f"Вы хотите изменить время задачи с {task['deadline']}. Пожалуйста, введите новый дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ:")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')