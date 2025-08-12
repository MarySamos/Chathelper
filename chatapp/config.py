import os
from typing import Optional
from pydantic_settings import BaseSettings


#企业微信配置
class Settings(BaseSettings):
 WEWORK_CORP_ID : str = os.getenv("WEWORK_CORP_ID", "ww4075a496788eac47")
 WEWORK_AGENT_ID : str = os.getenv("WEWORK_AGENT_ID", "1000002")
 WEWORK_SECRET : str = os.getenv("WEWORK_SECRET", "3KYlbSq-cHHsr-pboEE9SHm3TzqBwBsE4sTRvLsCqS8")
 WEWORK_TOKEN : str = os.getenv("WEWORK_TOKEN", "JA8EQPF")
 WEWORK_ENCODING_AES_KEY : str = os.getenv("WEWORK_ENCODING_AES_KEY", "XpSPZbYMaDBGd0F5fkTgmH3E55e3QRriB6EB8eoSssd")

#OPENAI配置
 OPENAI_API_KEY: str = os.getenv("APIKEY",
                                "")
 OPENAI_BASE_URL: str = os.getenv("BASEURL","https://api.openai.com/v1")
 OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

 # RAGFlow 配置
 RAGFLOW_API_URL: str = os.getenv("RAGFLOW_API_URL", "http://localhost:9870")
 RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "ragflow-dmZjViNzU4NmU3ZTExZjA4ZmIxOGFlNG")

 # Redis 配置
 REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
 REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
 REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD","root123")
 REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

 # Celery 配置
 CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
 CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

 # MYSQL 配置
 POSTGRES_HOST: str = os.getenv("MYSQL_HOST", "8.138.204.57")
 POSTGRES_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
 POSTGRES_DB: str = os.getenv("MYSQL_DB", "KKHourse")
 POSTGRES_USER: str = os.getenv("MYSQL_USER", "root")
 POSTGRES_PASSWORD: str = os.getenv("MYSQLPASSWORD", "Qkz12136")

 # 应用配置
 DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
 LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

 @property
 def database_url(self) -> str:
     return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()

