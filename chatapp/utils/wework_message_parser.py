#企业微信消息解析工具
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from chatapp.utils.logger import logger


class WeWorkMessageParser:
    """企业微信消息解析器"""

    @staticmethod
    def parse_message_xml(xml_content: str) -> Optional[Dict[str, Any]]:
        """
        解析企业微信消息XML

        Args:
            xml_content: 解密后的XML消息内容

        Returns:
            解析后的消息字典，如果解析失败返回None
        """
        try:
            root = ET.fromstring(xml_content)

            # 提取基本消息信息
            message_data = {
                "to_user_name": WeWorkMessageParser._get_xml_text(root, "ToUserName"),
                "from_user_name": WeWorkMessageParser._get_xml_text(root, "FromUserName"),
                "create_time": WeWorkMessageParser._get_xml_text(root, "CreateTime"),
                "msg_type": WeWorkMessageParser._get_xml_text(root, "MsgType"),
                "msg_id": WeWorkMessageParser._get_xml_text(root, "MsgId"),
                "agent_id": WeWorkMessageParser._get_xml_text(root, "AgentID")
            }

            # 根据消息类型解析具体内容
            msg_type = message_data.get("msg_type", "")

            if msg_type == "text":
                message_data["content"] = WeWorkMessageParser._get_xml_text(root, "Content")

            elif msg_type == "image":
                message_data.update({
                    "pic_url": WeWorkMessageParser._get_xml_text(root, "PicUrl"),
                    "media_id": WeWorkMessageParser._get_xml_text(root, "MediaId")
                })

            elif msg_type == "voice":
                message_data.update({
                    "media_id": WeWorkMessageParser._get_xml_text(root, "MediaId"),
                    "format": WeWorkMessageParser._get_xml_text(root, "Format")
                })

            elif msg_type == "video":
                message_data.update({
                    "media_id": WeWorkMessageParser._get_xml_text(root, "MediaId"),
                    "thumb_media_id": WeWorkMessageParser._get_xml_text(root, "ThumbMediaId")
                })

            elif msg_type == "file":
                message_data.update({
                    "media_id": WeWorkMessageParser._get_xml_text(root, "MediaId"),
                    "file_name": WeWorkMessageParser._get_xml_text(root, "FileName"),
                    "file_size": WeWorkMessageParser._get_xml_text(root, "FileSize")
                })

            elif msg_type == "location":
                message_data.update({
                    "location_x": WeWorkMessageParser._get_xml_text(root, "Location_X"),
                    "location_y": WeWorkMessageParser._get_xml_text(root, "Location_Y"),
                    "scale": WeWorkMessageParser._get_xml_text(root, "Scale"),
                    "label": WeWorkMessageParser._get_xml_text(root, "Label")
                })

            elif msg_type == "event":
                # 事件类型消息
                message_data.update({
                    "event": WeWorkMessageParser._get_xml_text(root, "Event"),
                    "event_key": WeWorkMessageParser._get_xml_text(root, "EventKey")
                })

            logger.info(f"Parsed WeWork message: type={msg_type}, from={message_data.get('from_user_name')}")
            return message_data

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing WeWork message: {e}")
            return None

    @staticmethod
    def _get_xml_text(root: ET.Element, tag_name: str) -> str:
        """安全地获取XML标签文本内容"""
        element = root.find(tag_name)
        return element.text if element is not None and element.text is not None else ""