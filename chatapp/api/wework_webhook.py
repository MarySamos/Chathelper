#企业微信回调API

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from chatapp.config import Settings
from chatapp.utils.wework_crypto import WeWorkOfficialCrypto
from chatapp.utils.wework_message_parser import WeWorkMessageParser
from chatapp.utils.logger import logger
from chatapp.workers.ai_worker import process_message
import time

router = APIRouter()

# 初始化官方加密工具
crypto = WeWorkOfficialCrypto()


@router.get("/wework/callback")
async def verify_callback(
        msg_signature: str = Query(...),
        timestamp: str = Query(...),
        nonce: str = Query(...),
        echostr: str = Query(...)
):
    """
    企业微信回调验证
    使用官方WXBizMsgCrypt库进行验证
    """
    try:
        logger.info(f"WeWork callback verification request: signature={msg_signature}, timestamp={timestamp}")

        # 使用官方库验证URL
        ret_code, echo_string = crypto.verify_url(msg_signature, timestamp, nonce, echostr)

        if ret_code == 0:
            logger.info("WeWork callback verification successful")
            return PlainTextResponse(echo_string)
        else:
            logger.error(f"WeWork callback verification failed with code: {ret_code}")
            raise HTTPException(status_code=403, detail=f"Verification failed: {ret_code}")

    except Exception as e:
        logger.error(f"Error in WeWork callback verification: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/wework/callback")
async def handle_message(
        request: Request,
        msg_signature: str = Query(...),
        timestamp: str = Query(...),
        nonce: str = Query(...)
):
    """
    处理企业微信消息回调
    使用官方WXBizMsgCrypt库进行消息解密
    """
    start_time = time.time()

    try:
        # 获取加密的XML数据
        body = await request.body()
        encrypted_xml = body.decode('utf-8')

        logger.info(f"Received WeWork message: signature={msg_signature}, timestamp={timestamp}")

        # 使用官方库解密消息
        ret_code, decrypted_xml = crypto.decrypt_msg(msg_signature, timestamp, nonce, encrypted_xml)

        if ret_code != 0:
            logger.error(f"WeWork message decryption failed with code: {ret_code}")
            raise HTTPException(status_code=400, detail=f"Decryption failed: {ret_code}")

        # 解析消息内容
        message_data = WeWorkMessageParser.parse_message_xml(decrypted_xml)

        if not message_data:
            logger.error("Failed to parse WeWork message")
            raise HTTPException(status_code=400, detail="Message parsing failed")

        # 添加时间戳
        message_data["received_time"] = int(time.time())

        # 快速响应企业微信 - 立即入队处理
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"WeWork message processed in {processing_time:.2f}ms, queuing for AI processing")

        # 异步处理消息 - 推送到Celery队列
        process_message.delay(message_data)

        # 立即返回成功响应
        return PlainTextResponse("success")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling WeWork message: {e}")
        raise HTTPException(status_code=500, detail="Message handling failed")