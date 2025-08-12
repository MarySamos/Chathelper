from celery import Celery
import asyncio
from typing import Dict, Any
from chatapp.config import settings
from chatapp.services.session_manager import SessionManager
from chatapp.services.ragflow_service import RAGFlowService
from chatapp.services.openai_service import OpenAIService
from chatapp.utils.logger import logger

# 创建 Celery 实例
celery_app = Celery(
    "ai_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_routes={
        'app.workers.ai_worker.process_message': {'queue': 'ai_processing'},
    }
)

# 初始化服务
session_manager = SessionManager()
ragflow_service = RAGFlowService()
openai_service = OpenAIService()


@celery_app.task(bind=True, max_retries=3)
def process_message(self, message_data: Dict[str, Any]):
    """
    处理消息的主要任务
    这是异步处理的核心，避免阻塞企业微信回调
    """
    try:
        logger.info(f"Processing message: {message_data.get('msg_id')}")

        # 运行异步处理逻辑
        result = asyncio.run(_process_message_async(message_data))

        logger.info(f"Message processed successfully: {message_data.get('msg_id')}")
        return result

    except Exception as e:
        logger.error(f"Error processing message {message_data.get('msg_id')}: {e}")

        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying message {message_data.get('msg_id')}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (self.request.retries + 1))  # 指数退避

        return {"error": str(e)}


async def _process_message_async(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """异步处理消息的核心逻辑"""

    # 提取消息信息
    from_user = message_data.get("from_user_name")
    to_user = message_data.get("to_user_name")  # 客服ID
    content = message_data.get("content")
    msg_type = message_data.get("msg_type")

    # 只处理文本消息
    if msg_type != "text":
        logger.info(f"Skipping non-text message: {msg_type}")
        return {"skipped": True, "reason": "non-text message"}

    try:
        # 1. 添加客户消息到会话上下文
        customer_message = {
            "content": content,
            "from_customer": True,
            "msg_type": msg_type
        }
        session_manager.add_message(to_user, from_user, customer_message)

        # 2. 获取会话上下文
        context = session_manager.get_context(to_user, from_user)

        # 3. 使用RAGFlow搜索相关知识
        knowledge_results = await ragflow_service.search_knowledge(content, top_k=5)

        # 4. 使用OpenAI生成回复建议
        suggestions = await openai_service.generate_suggestions(content, context, knowledge_results)

        # 5. 准备推送数据
        result_data = {
            "session_id": f"{to_user}:{from_user}",
            "customer_id": from_user,
            "agent_id": to_user,
            "customer_message": content,
            "suggestions": suggestions,
            "knowledge_results": knowledge_results[:3],  # 只返回前3条知识库结果
            "context_length": len(context),
            "timestamp": message_data.get("create_time")
        }

        # 6. 通过WebSocket推送给前端（这里先记录日志，实际推送在main.py中实现）
        logger.info(f"Generated suggestions for agent {to_user}: {len(suggestions)} items")

        # 7. 将结果存储到Redis，供WebSocket服务获取
        import json
        result_key = f"ai_result:{to_user}:{from_user}:{message_data.get('msg_id')}"
        session_manager.redis_client.setex(
            result_key,
            300,  # 5分钟过期
            json.dumps(result_data, ensure_ascii=False)
        )

        return result_data

    except Exception as e:
        logger.error(f"Error in async message processing: {e}")
        raise
