# Notification Worker for sending alerts
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import async_session_maker
from app.models import User, Report


async def send_notification(user_id: str, message: str, notification_type: str):
    # Placeholder: Implement actual push notifications (FCM, APNs) or email
    print(f"[NOTIFICATION] To: {user_id} | Type: {notification_type} | Message: {message}")


async def process_status_change(message: dict, db: AsyncSession):
    report_id = message.get("report_id")
    new_status = message.get("new_status")
    
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        return
    
    result = await db.execute(select(User).where(User.id == report.user_id))
    user = result.scalar_one_or_none()
    
    if user:
        await send_notification(
            str(user.id),
            f"Your report status has been updated to: {new_status}",
            "status_update"
        )


async def process_assignment(message: dict, db: AsyncSession):
    report_id = message.get("report_id")
    assigned_to = message.get("assigned_to")
    
    if assigned_to:
        await send_notification(
            assigned_to,
            f"You have been assigned a new report: {report_id}",
            "assignment"
        )


async def notification_worker():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_STATUS_CHANGED,
        settings.KAFKA_TOPIC_REPORT_ASSIGNED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-worker-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    print("Notification Worker started, listening for messages...")
    
    try:
        async for msg in consumer:
            if msg.topic == settings.KAFKA_TOPIC_STATUS_CHANGED:
                async with async_session_maker() as db:
                    await process_status_change(msg.value, db)
            elif msg.topic == settings.KAFKA_TOPIC_REPORT_ASSIGNED:
                async with async_session_maker() as db:
                    await process_assignment(msg.value, db)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(notification_worker())
