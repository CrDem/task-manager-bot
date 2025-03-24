import asyncio
import logging
from bot.config import bot, dp
from aiogram.filters import Command
from bot_handlers import start_command, show_tasks, add_task, process_message, edit_task, complete_task, \
    remove_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO)
    dp.message.register(start_command, Command(commands=["start"]))
    dp.message.register(show_tasks, Command(commands=["tasks"]))
    dp.message.register(add_task, Command(commands=["add_task"]))
    dp.message.register(edit_task, Command(commands=["edit_task"]))
    dp.message.register(complete_task, Command(commands=["complete_task"]))
    dp.message.register(remove_task, Command(commands=["remove_task"]))
    dp.message.register(process_message)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
