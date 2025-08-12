import httpx
from typing import List, Dict, Any
from chatapp.config import settings
from chatapp.utils.logger import logger


class RAGFlowService:
    """RAGFlow 知识库检索服务"""

    def __init__(self):
        self.api_url = settings.RAGFLOW_API_URL
        self.api_key = settings.RAGFLOW_API_KEY
        self.timeout = 30

    async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识库"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/api/v1/retrieval",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "top_k": top_k,
                        "dataset": "real_estate"  # 假设您的房源数据集名称
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"RAGFlow search successful for query: {query}")
                    return result.get("data", [])
                else:
                    logger.error(f"RAGFlow search failed: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error searching RAGFlow: {e}")
            return []
