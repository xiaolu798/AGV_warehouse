import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        # 存放所有活跃的连接
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"新的监控连接进入，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("监控连接已断开")

    async def broadcast(self, message: dict):
        """
        核心广播功能：将字典转化为 JSON 字符串发送
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # 如果某个连接失效，自动清理
                print(f"发送失败，清理失效连接: {e}")
                self.active_connections.remove(connection)


# 实例化管理器，供全局使用
ws_manager = ConnectionManager()
