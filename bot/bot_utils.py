import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import bot
from database_utils import user_states_collection

logging.basicConfig(level=logging.INFO)


# manage functions
async def main_menu(chat_id):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Показать задачи", callback_data="show_tasks")],
        [InlineKeyboardButton(text="✏ Управление задачами", callback_data="manage_tasks")]
    ])
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)


async def clear_chat(message: Message, skipThisMessage: int = 1):
    chat_id = message.chat.id
    try:
        for i in range(message.message_id - skipThisMessage, message.message_id - 100,
                       -1):  # Удаляем последние 100 сообщений
            try:
                await bot.delete_message(chat_id, i)
            except Exception:
                break
    except Exception as e:
        logging.warning(f"Ошибка при очистке чата: {e}")


async def clear_state(user_id: int):
    if user_states_collection.find_one({"user_id": user_id}):
        user_states_collection.delete_one({"user_id": user_id})
