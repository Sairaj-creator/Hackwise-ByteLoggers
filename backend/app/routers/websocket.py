"""
WebSocket Router
=================
Real-time trending recipes and community updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List
import json
import asyncio

from app.dependencies import decode_token

router = APIRouter(tags=["WebSocket"])

# ─── Connection Manager ───

class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ─── WebSocket Endpoint ───

@router.websocket("/api/v1/ws/trends")
async def websocket_trends(websocket: WebSocket, token: str = Query(default="")):
    # Validate token
    if token:
        try:
            decode_token(token)
        except Exception:
            await websocket.close(code=1008)
            return

    await manager.connect(websocket)

    try:
        while True:
            # Listen for client messages (heartbeat)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_json({"event": "pong"})
            except asyncio.TimeoutError:
                # Send a periodic trending update
                await websocket.send_json({
                    "event": "trending_ingredient",
                    "data": {
                        "ingredient": "Mango",
                        "users_cooking": 47,
                        "city": "Bengaluru",
                        "trending_recipes": ["Mango Lassi", "Aam Panna"],
                    },
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# ─── Broadcast helper (called from other services) ───

async def broadcast_new_recipe(recipe_title: str, author_name: str, recipe_id: str):
    """Broadcast a new community recipe to all connected clients."""
    await manager.broadcast({
        "event": "new_community_recipe",
        "data": {
            "recipe_id": recipe_id,
            "title": recipe_title,
            "author": author_name,
            "likes": 0,
        },
    })
