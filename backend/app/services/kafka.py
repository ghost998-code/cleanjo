import json
import asyncio
from typing import Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from app.core.config import settings


class KafkaService:
    _producer: Optional[AIOKafkaProducer] = None
    _consumers: dict = {}

    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        if cls._producer is None:
            cls._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            await cls._producer.start()
        return cls._producer

    @classmethod
    async def stop_producer(cls):
        if cls._producer:
            await cls._producer.stop()
            cls._producer = None

    @classmethod
    async def send_message(cls, topic: str, message: dict):
        producer = await cls.get_producer()
        await producer.send_and_wait(topic, message)

    @classmethod
    async def create_consumer(cls, topic: str, group_id: str) -> AIOKafkaConsumer:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await consumer.start()
        return consumer


kafka_service = KafkaService()
