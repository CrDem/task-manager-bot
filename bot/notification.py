import asyncio
import logging
from datetime import datetime, timedelta
from celery import Celery
from bot.config import bot
from bot.database_utils import tasks_collection
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

@celery_app.task(name="check_expired_tasks_and_prolong")
def check_expired_tasks_and_prolong():
    """
    Проходит по БД, находит задачи с истекшим дедлайном, продлевает на 1 день,
    если еще не были продлены ранее (extended=False). Если задача была удалена, уведомление не отправляется.
    """
    now = datetime.now()

    expired_tasks = tasks_collection.find({"deadline": {"$lt": now}, "extended": False})

    for task in expired_tasks:
        task_id = task["_id"]
        user_id = task["user_id"]
        task_text = task["text"]
        old_deadline = task["deadline"]

        new_deadline = old_deadline + timedelta(days=1)
        result = tasks_collection.update_one(
            {"_id": task_id, "extended": False},
            {"$set": {"deadline": new_deadline, "extended": True}}
        )

        if result.modified_count > 0:
            notification_text = (
                f"⏳ Ваша задача '{task_text}' имела истекший срок выполнения. "
                f"Срок продлен на 1 день. Новый дедлайн: {new_deadline.strftime('%Y-%m-%d %H:%M:%S')}."
            )

            try:
                asyncio.run(send_async_notification(user_id, notification_text))
                logger.info(f"Уведомление отправлено пользователю {user_id} о продлении задачи {task_id}.")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления для задачи {task_id}: {e}")
        else:
            logger.info(f"Задача {task_id} не найдена или уже была продлена.")


celery_app.conf.beat_schedule = {
    "check-expired-tasks-every-5-minutes": {
        "task": "check_expired_tasks_and_prolong",
        "schedule": 120,
    },
}









