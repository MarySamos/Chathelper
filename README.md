# Chathelper
├── chatapp/
│   ├── __init__.py
│   ├── main.py                 
│   ├── config.py              # 配置文件
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         
│   ├── services/
│   │   ├── __init__.py
│   │   ├── wework_service.py  # 企业微信服务
│   │   ├── ragflow_service.py
│   │   ├── openai_service.py  
│   │   └── session_manager.py 
│   ├── workers/
│   │   ├── __init__.py
│   │   └── ai_worker.py       # AI对话单元
│   ├── api/
│   │   ├── __init__.py
│   │   └── wework_webhook.py  # 企业微信回调API 利用官方WXBizMsgCrypt库进行消息解密 ？？需要回调URL？
│   └── utils/
│       ├── __init__.py
│       ├── crypto.py          # 加密解密工具
│       └── logger.py          # 日志工具
└── README.md

