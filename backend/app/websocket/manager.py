from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, payload: dict, websocket: WebSocket) -> None:
        await websocket.send_json(payload)

    async def broadcast(self, payload: dict) -> None:
        for conn in list(self.active_connections):
            await conn.send_json(payload)


manager = ConnectionManager()