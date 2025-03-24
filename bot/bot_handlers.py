from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot_utils import main_menu, clear_state,clear_chat
from bot.config import bot, dp
from bson import ObjectId
from notification import schedule_notification,revoke_notification
from datetime import datetime
from database_utils import tasks_collection, user_states_collection

# command functions
@dp.message(F.text == "/start")
async def start_command(message: Message):
    await clear_state(message.from_user.id)
    await clear_chat(message, 0)
    await main_menu(message.chat.id)

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

# manage functions
@dp.callback_query(F.data == "add_task")
async def add_task(callback: CallbackQuery):
    user_states_collection.update_one({"user_id": callback.from_user.id}, {"$set": {"state": "waiting_for_deadline"}}, upsert=True)
    await bot.send_message(callback.message.chat.id, "Введите дедлайн задачи в формате ГГГГ-ММ-ДД ЧЧ:ММ:")

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
            "completed": False,
            "extended": False

        }
        tasks_collection.insert_one(task)
        task_id = task["_id"]
        celery_task_id = schedule_notification(user_id, message.text, user_state["deadline"])
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
            task_record = tasks_collection.find_one({"_id": ObjectId(task_id)})

            old_celery_task_id = task_record.get("celery_task_id")
            revoke_notification(old_celery_task_id)
            new_celery_task_id = schedule_notification(user_id, task_record["text"], new_deadline)

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

@dp.callback_query(F.data.startswith("complete_"))
async def complete_task(callback: CallbackQuery):
    task_id = callback.data.split("_")[1]
    tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": True}})
    await callback.answer("✅ Задача отмечена как выполненная.", show_alert=True)
    await manage_tasks(callback)

@dp.callback_query(F.data.startswith("remove_task_"))
async def remove_task(callback: CallbackQuery):
    task_id = callback.data.split("_")[2]
    task_record = tasks_collection.find_one({"_id": ObjectId(task_id)})
    celery_task_id = task_record.get("celery_task_id")
    revoke_notification(celery_task_id)
    tasks_collection.delete_one({"_id": ObjectId(task_id)})
    await callback.answer("🗑 Задача удалена.", show_alert=True)
    await manage_tasks(callback)

@dp.callback_query(F.data.startswith("change_text_"))
async def change_text(callback: CallbackQuery):
    task_id = callback.data.split("_")[2]  # Извлекаем task_id
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        await callback.answer("⚠ Задача не найдена.", show_alert=True)
        return

    user_states_collection.update_one({"user_id": callback.from_user.id}, {"$set": {"state": "waiting_for_new_text", "task_changing_id": task_id}}, upsert=True)
    await callback.message.edit_text(f"Вы хотите изменить текст задачи: {task['text']}. Пожалуйста, введите новый текст задачи:")

@dp.callback_query(F.data.startswith("change_time_"))
async def change_time(callback: CallbackQuery):
    task_id = callback.data.split("_")[2]  # Извлекаем task_id
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        await callback.answer("⚠ Задача не найдена.", show_alert=True)
        return

    user_states_collection.update_one({"user_id": callback.from_user.id}, {"$set": {"state": "waiting_for_new_deadline", "task_changing_id": task_id}}, upsert=True)
    await callback.message.edit_text(f"Вы хотите изменить время задачи с {task['deadline']}. Пожалуйста, введите новый дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ:")

# postavte >= 9 plz


