import logging
import sys
from chatapp.config import settings

def setup_logger():
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()