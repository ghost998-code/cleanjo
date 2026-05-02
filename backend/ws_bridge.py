import asyncio
import json
import logging
from contextlib import suppress
from collections import deque
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.core.security import decode_token
from app.core.constants import UserRole
from app.core.database import async_session_maker
from app.models import User
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ws_bridge")

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.user_roles: dict[str, str] = {}
        self.recent_events: deque[dict] = deque(maxlen=200)

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.user_roles[user_id] = role

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            with suppress(ValueError):
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.user_roles.pop(user_id, None)

    async def send_personal_message(self, message: dict, user_id: str):
        connections = self.active_connections.get(user_id, [])
        stale_connections = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection, user_id)

    async def send_report_event(self, message: dict):
        data = message.get("data") or {}
        owner_id = str(data.get("user_id")) if data.get("user_id") else None
        assigned_to = str(data.get("assigned_to")) if data.get("assigned_to") else None

        for user_id, role in list(self.user_roles.items()):
            if role == UserRole.ADMIN.value:
                await self.send_personal_message(message, user_id)
                continue
            if owner_id and user_id == owner_id:
                await self.send_personal_message(message, user_id)
                continue
            if assigned_to and user_id == assigned_to:
                await self.send_personal_message(message, user_id)

    async def send_recent_events(self, user_id: str):
        role = self.user_roles.get(user_id)
        if not role:
            return
        for message in list(self.recent_events):
            data = message.get("data") or {}
            owner_id = str(data.get("user_id")) if data.get("user_id") else None
            assigned_to = str(data.get("assigned_to")) if data.get("assigned_to") else None
            if role == UserRole.ADMIN.value or user_id == owner_id or user_id == assigned_to:
                await self.send_personal_message(message, user_id)

manager = ConnectionManager()


async def resolve_user_role(user_id: str, payload: dict) -> str | None:
    payload_role = payload.get("role")
    if isinstance(payload_role, str):
        return payload_role

    async with async_session_maker() as db:
        result = await db.execute(select(User.role).where(User.id == user_id))
        role = result.scalar_one_or_none()
        return role.value if role is not None else None

async def kafka_consumer():
    consumer = AIOKafkaConsumer(
        "report.events",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="ws-bridge-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for msg in consumer:
            logger.info(f"Received Kafka event: {msg.value}")
            manager.recent_events.append(msg.value)
            await manager.send_report_event(msg.value)
    finally:
        await consumer.stop()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_consumer())

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Minimal auth check
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008)
        return
    role = await resolve_user_role(str(user_id), payload)
    if not role:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket, str(user_id), role)
    await manager.send_recent_events(str(user_id))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, str(user_id))
