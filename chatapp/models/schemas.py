from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class WeWorkMessage(BaseModel):
    """企业微信消息模型"""
    msg_id: str
    from_user: str
    to_user: str
    msg_type: str
    content: str
    agent_id: str
    create_time: int

class ChatContext(BaseModel):
    """聊天上下文模型"""
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class AIResponse(BaseModel):
    """AI 回复建议模型"""
    session_id: str
    suggestions: List[str]
    confidence: float
    generated_at: datetime

class RAGResult(BaseModel):
    """RAG 检索结果模型"""
    query: str
    results: List[Dict[str, Any]]
    score: float