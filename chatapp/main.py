# app/main.py - 更新主应用文件
# ============================================================================
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from chatapp.api.wework_webhook import router as wework_router
from chatapp.config import settings
from chatapp.utils.logger import logger
import json
import asyncio
from typing import Dict, Set

# 创建FastAPI应用
app = FastAPI(
    title="WeWork AI Assistant",
    description="企业微信智能客服助手",
    version="1.0.0"
)

# 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_sessions: Dict[str, Set[str]] = {}  # agent_id -> set of session_ids

    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        logger.info(f"WebSocket connected for agent: {agent_id}")

    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in self.agent_sessions:
            del self.agent_sessions[agent_id]
        logger.info(f"WebSocket disconnected for agent: {agent_id}")

    async def send_personal_message(self, message: str, agent_id: str):
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to agent {agent_id}: {e}")
                return False
        return False


manager = ConnectionManager()

# 注册路由
app.include_router(wework_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "WeWork AI Assistant",
        "version": "1.0.0"
    }


@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket连接端点"""
    await manager.connect(websocket, agent_id)

    try:
        while True:
            # 接收心跳或其他客户端消息
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
                continue

            # 处理其他类型的消息（如客服反馈等）
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")

                if message_type == "feedback":
                    # 处理客服对AI建议的反馈
                    logger.info(f"Received feedback from agent {agent_id}: {message_data}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from agent {agent_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(agent_id)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("WeWork AI Assistant starting up...")

    # 这里可以添加启动时的初始化逻辑
    # 比如检查外部服务连接等


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("WeWork AI Assistant shutting down...")