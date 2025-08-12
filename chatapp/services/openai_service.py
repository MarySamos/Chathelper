import httpx
from typing import List, Dict, Any
from chatapp.config import settings
from chatapp.utils.logger import logger


class OpenAIService:
    """OpenAI 服务"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL
        self.timeout = 60

    def build_prompt(self, query: str, context: List[Dict[str, Any]], knowledge: List[Dict[str, Any]]) -> str:
        """构建 Prompt"""
        system_prompt = """你是一个专业的房产销售顾问助手，你的任务是帮助客服人员生成专业、热情且准确的回复建议。

## 角色要求：
- 热情专业，善于倾听客户需求
- 基于知识库信息提供准确答案
- 避免过度承诺，诚实回答不确定的问题
- 引导客户进一步沟通，促成线下面谈

## 输出要求：
请根据客户问题和提供的知识库信息，生成3条不同风格的回复建议：
1. 简洁直接型：直接回答问题，言简意赅
2. 热情详细型：提供详细信息，展现专业性
3. 引导询问型：通过反问了解更多需求，引导深入沟通

每条建议用 "建议1:"、"建议2:"、"建议3:" 开头，换行分隔。"""

        # 构建对话历史
        context_str = ""
        if context:
            context_str = "\n## 对话历史：\n"
            for msg in context[-5:]:  # 只取最近5条
                role = "客户" if msg.get("from_customer") else "客服"
                context_str += f"{role}：{msg.get('content', '')}\n"

        # 构建知识库信息
        knowledge_str = ""
        if knowledge:
            knowledge_str = "\n## 相关知识库信息：\n"
            for i, item in enumerate(knowledge[:3], 1):  # 只取前3条最相关的
                content = item.get("content", "")
                knowledge_str += f"{i}. {content}\n"

        # 当前客户问题
        current_query = f"\n## 当前客户问题：\n{query}\n"

        prompt = system_prompt + context_str + knowledge_str + current_query
        return prompt

    async def generate_suggestions(self, query: str, context: List[Dict[str, Any]], knowledge: List[Dict[str, Any]]) -> \
    List[str]:
        """生成回复建议"""
        try:
            prompt = self.build_prompt(query, context, knowledge)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # 解析建议
                    suggestions = self.parse_suggestions(content)
                    logger.info(f"Generated {len(suggestions)} suggestions for query: {query}")
                    return suggestions
                else:
                    logger.error(f"OpenAI API failed: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []

    def parse_suggestions(self, content: str) -> List[str]:
        """解析AI生成的建议"""
        suggestions = []
        lines = content.split('\n')
        current_suggestion = ""

        for line in lines:
            line = line.strip()
            if line.startswith(('建议1:', '建议2:', '建议3:')):
                if current_suggestion:
                    suggestions.append(current_suggestion.strip())
                current_suggestion = line[3:].strip()  # 移除"建议X:"前缀
            elif current_suggestion and line:
                current_suggestion += " " + line

        if current_suggestion:
            suggestions.append(current_suggestion.strip())

        return suggestions