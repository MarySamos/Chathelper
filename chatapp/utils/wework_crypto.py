
# app/utils/wework_crypto.py - 使用官方WXBizMsgCrypt库
# ============================================================================
from chatapp.callback.WXBizMsgCrypt3 import WXBizMsgCrypt
from chatapp.config import settings
from chatapp.utils.logger import logger
import xml.etree.ElementTree as ET
from typing import Tuple, Optional


class WeWorkOfficialCrypto:
    """企业微信官方加密解密工具类"""

    def __init__(self):
        self.token = settings.WEWORK_TOKEN
        self.encoding_aes_key = settings.WEWORK_ENCODING_AES_KEY
        self.corp_id = settings.WEWORK_CORP_ID

        # 初始化官方加密库
        self.wxcrypt = WXBizMsgCrypt(
            sToken=self.token,
            sEncodingAESKey=self.encoding_aes_key,
            sReceiveId=self.corp_id
        )

        logger.info("WeWork official crypto initialized")

    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> Tuple[int, str]:
        """
        验证URL有效性（企业微信回调验证）

        Args:
            msg_signature: 签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 加密的随机字符串

        Returns:
            (ret_code, echo_string): 返回码和解密后的字符串
        """
        try:
            ret, sEchoStr = self.wxcrypt.VerifyURL(msg_signature, timestamp, nonce, echostr)

            if ret == 0:
                logger.info("WeWork URL verification successful")
                return ret, sEchoStr
            else:
                logger.error(f"WeWork URL verification failed with code: {ret}")
                return ret, ""

        except Exception as e:
            logger.error(f"Error in WeWork URL verification: {e}")
            return -1, ""

    def decrypt_msg(self, msg_signature: str, timestamp: str, nonce: str, encrypted_xml: str) -> Tuple[int, str]:
        """
        解密消息

        Args:
            msg_signature: 签名
            timestamp: 时间戳
            nonce: 随机数
            encrypted_xml: 加密的XML消息

        Returns:
            (ret_code, decrypted_xml): 返回码和解密后的XML
        """
        try:
            ret, sMsg = self.wxcrypt.DecryptMsg(encrypted_xml, msg_signature, timestamp, nonce)

            if ret == 0:
                logger.info("WeWork message decryption successful")
                return ret, sMsg
            else:
                logger.error(f"WeWork message decryption failed with code: {ret}")
                return ret, ""

        except Exception as e:
            logger.error(f"Error in WeWork message decryption: {e}")
            return -1, ""

    def encrypt_msg(self, reply_msg: str, nonce: str, timestamp: str) -> Tuple[int, str]:
        """
        加密回复消息（如果需要主动发送消息）

        Args:
            reply_msg: 要发送的消息
            nonce: 随机数
            timestamp: 时间戳

        Returns:
            (ret_code, encrypted_xml): 返回码和加密后的XML
        """
        try:
            ret, sEncryptMsg = self.wxcrypt.EncryptMsg(reply_msg, nonce, timestamp)

            if ret == 0:
                logger.info("WeWork message encryption successful")
                return ret, sEncryptMsg
            else:
                logger.error(f"WeWork message encryption failed with code: {ret}")
                return ret, ""

        except Exception as e:
            logger.error(f"Error in WeWork message encryption: {e}")
            return -1, ""