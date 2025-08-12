import httpx
import json
from typing import Optional, Dict, Any
from chatapp.config import settings
from chatapp.utils.logger import logger
from chatapp.utils.wework_crypto import WeWorkOfficialCrypto
import time


class WeWorkService:
    """企业微信服务 - 支持官方加密库"""

    def __init__(self):
        self.corp_id = settings.WEWORK_CORP_ID
        self.secret = settings.WEWORK_SECRET
        self.agent_id = settings.WEWORK_AGENT_ID
        self.access_token = None
        self.token_expires_at = 0
        self.timeout = 30
        self.crypto = WeWorkOfficialCrypto()

    async def get_access_token(self) -> Optional[str]:
        """获取访问令牌（带缓存）"""
        # 检查token是否仍然有效
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                    params={
                        "corpid": self.corp_id,
                        "corpsecret": self.secret
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        self.access_token = result.get("access_token")
                        expires_in = result.get("expires_in", 7200)  # 默认2小时
                        self.token_expires_at = time.time() + expires_in - 300  # 提前5分钟过期

                        logger.info(f"WeWork access token obtained, expires in {expires_in}s")
                        return self.access_token
                    else:
                        logger.error(f"WeWork API error: {result}")
                        return None

        except Exception as e:
            logger.error(f"Error getting WeWork access token: {e}")
            return None

    async def send_text_message(self, user_id: str, content: str) -> bool:
        """发送文本消息"""
        if not await self.get_access_token():
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                    params={"access_token": self.access_token},
                    json={
                        "touser": user_id,
                        "msgtype": "text",
                        "agentid": self.agent_id,
                        "text": {"content": content}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        logger.info(f"Text message sent successfully to {user_id}")
                        return True
                    else:
                        logger.error(f"WeWork send message error: {result}")
                        return False

        except Exception as e:
            logger.error(f"Error sending text message: {e}")
            return False

    async def send_markdown_message(self, user_id: str, content: str) -> bool:
        """发送Markdown消息"""
        if not await self.get_access_token():
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                    params={"access_token": self.access_token},
                    json={
                        "touser": user_id,
                        "msgtype": "markdown",
                        "agentid": self.agent_id,
                        "markdown": {"content": content}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        logger.info(f"Markdown message sent successfully to {user_id}")
                        return True
                    else:
                        logger.error(f"WeWork send markdown message error: {result}")
                        return False

        except Exception as e:
            logger.error(f"Error sending markdown message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        if not await self.get_access_token():
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://qyapi.weixin.qq.com/cgi-bin/user/get",
                    params={
                        "access_token": self.access_token,
                        "userid": user_id
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        logger.info(f"User info retrieved for {user_id}")
                        return result
                    else:
                        logger.error(f"WeWork get user info error: {result}")
                        return None

        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None