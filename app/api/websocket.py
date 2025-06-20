from typing import List

from fastapi import APIRouter, WebSocket

router = APIRouter()
active_connections: List[WebSocket] = []


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # 保持连接
    except Exception:
        pass
    finally:
        active_connections.remove(websocket)
