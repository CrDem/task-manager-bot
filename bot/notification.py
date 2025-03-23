import asyncio
import logging
from datetime import datetime, timedelta
from celery import Celery
from config import bot
# from celery.schedules import crontab
# from bot.database_utils import tasks_collection
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery('notification', broker='amqp://guest:guest@localhost:5672//')


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
        return task.id
    return None


def revoke_notification(task_id):
    """Отменяет задачу по её ID."""
    celery_app.control.revoke(task_id, terminate=True)
    logger.info(f"Задача {task_id} удалена")

# celery_app.conf.beat_schedule = {
#     'check-deadlines-every-5-minutes': {  # Имя расписания
#         'task': 'bot.check_deadlines',  # Имя Celery задачи
#         'schedule': timedelta(seconds=10)
#   # Каждые 5 минут
#     }
# }
# celery_app.conf.timezone = 'UTC'
#
# @celery_app.task(name='bot.check_deadlines')
# def check_deadlines():
#     """
#     Проверяет истёкшие задачи и продлевает дедлайн.
#     """
#     try:
#         now = datetime.now()
#
#         # Ищем задачи с истёкшим дедлайном
#         tasks = tasks_collection.find({
#             "deadline": {"$lt": now},  # Дедлайн истёк
#             "completed": False,  # Задача не выполнена
#             "extended": False  # Ещё не была продлена
#         })
#
#         for task in tasks:
#             task_id = task["_id"]
#             user_id = task["user_id"]
#             try:
#                 # Проверяем, не была ли задача удалена (или снова что-то изменилось)
#                 task = tasks_collection.find_one({"_id": task_id})
#                 if not task:
#                     logger.info(f"Задача {task_id} была удалена. Пропускаем.")
#                     continue
#
#                 # Продлеваем дедлайн на сутки
#                 new_deadline = task["deadline"] + timedelta(days=1)
#                 tasks_collection.update_one(
#                     {"_id": task_id},
#                     {"$set": {
#                         "deadline": new_deadline,
#                         "extended": True
#                     }}
#                 )
#
#                 # Уведомляем пользователя о продлении
#                 text = (
#                     f"Срок вашей задачи '{task['title']}' истёк. Мы продлили её на 1 день.\n"
#                     f"Новый дедлайн: {new_deadline.strftime('%Y-%m-%d %H:%M')}"
#                 )
#                 asyncio.run(send_async_notification(user_id, text))
#                 logger.info(f"Продлили задачу {task_id} до {new_deadline} для пользователя {user_id}.")
#             except Exception as e:
#                 logger.error(f"Ошибка обработки задачи {task_id}: {e}")
#     except Exception as e:
#         logger.error(f"Ошибка проверки дедлайнов: {e}")

