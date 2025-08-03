from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException, status
from fastapi.routing import APIRouter
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
from datetime import datetime
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.services.auth import AuthService
from app.models.user import User

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃的WebSocket连接 {user_id: websocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # 存储用户房间 {user_id: room_id}
        self.user_rooms: Dict[int, str] = {}
        # 反向映射 {room_id: user_id}
        self.room_users: Dict[str, int] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, room_id: str = None):
        """接受WebSocket连接并添加到管理器"""
        await websocket.accept()
        
        # 如果用户已经有连接，先断开旧连接
        if user_id in self.active_connections:
            try:
                old_websocket = self.active_connections[user_id]
                await old_websocket.close()
            except Exception as e:
                logger.warning(f"关闭旧连接失败: {e}")
        
        # 添加新连接
        self.active_connections[user_id] = websocket
        
        # 设置房间（默认为用户ID）
        room_id = room_id or f"user_{user_id}"
        self.user_rooms[user_id] = room_id
        self.room_users[room_id] = user_id
        
        logger.info(f"用户 {user_id} 连接到房间 {room_id}")
        
        # 发送连接成功消息
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket连接成功",
            "room_id": room_id,
            "timestamp": datetime.now().isoformat()
        }, user_id)
    
    def disconnect(self, user_id: int):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.user_rooms:
            room_id = self.user_rooms[user_id]
            del self.user_rooms[user_id]
            if room_id in self.room_users:
                del self.room_users[room_id]
        
        logger.info(f"用户 {user_id} 断开连接")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """向特定用户发送消息"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                return True
            except Exception as e:
                logger.error(f"发送消息失败给用户 {user_id}: {e}")
                # 连接可能已断开，清理连接
                self.disconnect(user_id)
                return False
        return False
    
    async def send_to_room(self, message: Dict[str, Any], room_id: str):
        """向房间内的用户发送消息"""
        if room_id in self.room_users:
            user_id = self.room_users[room_id]
            return await self.send_personal_message(message, user_id)
        return False
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """向所有连接的用户广播消息"""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败给用户 {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    def get_connected_users(self) -> List[int]:
        """获取所有连接的用户ID"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: int) -> bool:
        """检查用户是否已连接"""
        return user_id in self.active_connections
    
    def get_user_room(self, user_id: int) -> Optional[str]:
        """获取用户所在房间"""
        return self.user_rooms.get(user_id)


# 全局连接管理器实例
manager = ConnectionManager()

# WebSocket路由
ws_router = APIRouter()


async def authenticate_websocket_user(websocket: WebSocket, token: str = None) -> Optional[User]:
    """WebSocket连接认证"""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return None
    
    try:
        # 解码JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return None
        
        # 获取用户信息
        db = next(get_db())
        try:
            auth_service = AuthService(db)
            user = auth_service.get_user_by_username(username)
            if user is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
                return None
            return user
        finally:
            db.close()
            
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return None
    except Exception as e:
        logger.error(f"WebSocket认证错误: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
        return None


@ws_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证token")
):
    """WebSocket端点"""
    # 认证用户
    user = await authenticate_websocket_user(websocket, token)
    if not user:
        return
    
    # 建立连接
    room_id = f"user_{user.id}"
    await manager.connect(websocket, user.id, room_id)
    
    try:
        # 心跳检测循环
        heartbeat_task = asyncio.create_task(heartbeat_loop(websocket, user.id))
        
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                await handle_websocket_message(websocket, user, message)
                
            except WebSocketDisconnect:
                logger.info(f"用户 {user.id} WebSocket断开连接")
                break
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }, user.id)
            except Exception as e:
                logger.error(f"WebSocket消息处理错误: {e}")
                await manager.send_personal_message({
                    "type": "error", 
                    "message": "Message processing error",
                    "timestamp": datetime.now().isoformat()
                }, user.id)
    
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        # 清理连接
        heartbeat_task.cancel()
        manager.disconnect(user.id)


async def handle_websocket_message(websocket: WebSocket, user: User, message: Dict[str, Any]):
    """处理WebSocket消息"""
    message_type = message.get("type", "")
    
    if message_type == "ping":
        # 心跳响应
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, user.id)
        
    elif message_type == "subscribe":
        # 订阅特定任务更新
        task_id = message.get("task_id")
        if task_id:
            await manager.send_personal_message({
                "type": "subscribed",
                "task_id": task_id,
                "message": f"已订阅任务 {task_id} 的更新",
                "timestamp": datetime.now().isoformat()
            }, user.id)
    
    elif message_type == "get_status":
        # 获取连接状态
        await manager.send_personal_message({
            "type": "status",
            "user_id": user.id,
            "room_id": manager.get_user_room(user.id),
            "connected_at": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        }, user.id)
    
    else:
        # 未知消息类型
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.now().isoformat()
        }, user.id)


async def heartbeat_loop(websocket: WebSocket, user_id: int):
    """心跳检测循环"""
    try:
        while True:
            await asyncio.sleep(30)  # 每30秒发送一次心跳
            try:
                await manager.send_personal_message({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }, user_id)
            except Exception as e:
                logger.error(f"心跳发送失败 用户 {user_id}: {e}")
                break
    except asyncio.CancelledError:
        logger.info(f"心跳任务取消 用户 {user_id}")
    except Exception as e:
        logger.error(f"心跳循环错误 用户 {user_id}: {e}")


# 导出管理器供其他模块使用
__all__ = ["manager", "ws_router"]