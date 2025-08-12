import json
import redis
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from chatapp.config import settings
from chatapp.utils.logger import logger


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.session_expire = 3600  # 1小时过期
        self.max_context_messages = 10  # 最多保存10条上下文

    def get_session_key(self, agent_id: str, customer_id: str) -> str:
        """生成会话键"""
        return f"session:{agent_id}:{customer_id}"

    def add_message(self, agent_id: str, customer_id: str, message: Dict[str, Any]):
        """添加消息到会话上下文"""
        session_key = self.get_session_key(agent_id, customer_id)

        try:
            # 获取现有上下文
            context = self.get_context(agent_id, customer_id)

            # 添加新消息
            message['timestamp'] = datetime.now().isoformat()
            context.append(message)

            # 保持上下文长度限制
            if len(context) > self.max_context_messages:
                context = context[-self.max_context_messages:]

            # 保存到 Redis
            self.redis_client.setex(
                session_key,
                self.session_expire,
                json.dumps(context, ensure_ascii=False)
            )

            logger.info(f"Added message to session {session_key}")

        except Exception as e:
            logger.error(f"Error adding message to session {session_key}: {e}")

    def get_context(self, agent_id: str, customer_id: str) -> List[Dict[str, Any]]:
        """获取会话上下文"""
        session_key = self.get_session_key(agent_id, customer_id)

        try:
            context_json = self.redis_client.get(session_key)
            if context_json:
                return json.loads(context_json)
            return []
        except Exception as e:
            logger.error(f"Error getting context for session {session_key}: {e}")
            return []

    def clear_session(self, agent_id: str, customer_id: str):
        """清除会话"""
        session_key = self.get_session_key(agent_id, customer_id)
        self.redis_client.delete(session_key)
