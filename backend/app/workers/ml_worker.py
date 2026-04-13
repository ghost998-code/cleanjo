# ML Worker for garbage classification
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import async_session_maker


async def process_message(message: dict, db: AsyncSession):
    from app.models import Report
    from sqlalchemy import select, update
    
    report_id = message.get("report_id")
    if not report_id:
        return
    
    print(f"Processing report: {report_id}")
    
    # Placeholder for ML inference
    # In production, load TensorFlow model and classify
    garbage_types = [
        "plastic", "paper", "glass", "metal", 
        "organic", "electronic", "mixed"
    ]
    import random
    predicted_type = random.choice(garbage_types)
    
    severity_map = {"plastic": "medium", "paper": "low", "glass": "medium", 
                    "metal": "medium", "organic": "high", "electronic": "critical",
                    "mixed": "medium"}
    
    await db.execute(
        update(Report)
        .where(Report.id == report_id)
        .values(garbage_type=predicted_type, severity=severity_map.get(predicted_type, "medium"))
    )
    await db.commit()
    print(f"Classified report {report_id} as {predicted_type}")


async def ml_worker():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_REPORT_CREATED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="ml-worker-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    print("ML Worker started, listening for messages...")
    
    try:
        async for msg in consumer:
            async with async_session_maker() as db:
                await process_message(msg.value, db)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(ml_worker())
