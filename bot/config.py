import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Создаем экземпляры Bot и Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()
