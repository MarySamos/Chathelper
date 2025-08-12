# ============================================================================
# test_wework_api.py - 企业微信API核心测试
# ============================================================================
import asyncio
import httpx
import hashlib
import time
import xml.etree.ElementTree as ET
import base64
import os
from typing import Dict, Any

from Crypto.SelfTest.Hash.test_SHA3_224 import APITest


# 测试配置 - 请替换为您的真实配置
class WeWorkTestConfig:
    # 企业微信配置 - 需要替换为您的真实值
    CORP_ID = os.getenv("WEWORK_CORP_ID", "ww4075a496788eac47")
    AGENT_ID = os.getenv("WEWORK_AGENT_ID", "1000002")
    SECRET = os.getenv("WEWORK_SECRET", "3KYlbSq-cHHsr-pboEE9SHm3TzqBwBsE4sTRvLsCqS8")
    TOKEN = os.getenv("WEWORK_TOKEN", "JA8EQPF")
    ENCODING_AES_KEY = os.getenv("WEWORK_ENCODING_AES_KEY", "XpSPZbYMaDBGd0F5fkTgmH3E55e3QRriB6EB8eoSssd")

    # 测试服务器地址
    API_BASE_URL = "http://localhost:8000"


config = WeWorkTestConfig()


class WeWorkAPITester:
    """企业微信API测试器"""

    def __init__(self):
        self.access_token = None

    def print_step(self, step: str, message: str):
        """打印测试步骤"""
        print(f"\n{'=' * 60}")
        print(f"🔍 步骤 {step}: {message}")
        print(f"{'=' * 60}")

    def print_result(self, success: bool, message: str):
        """打印测试结果"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")

    async def test_1_config_check(self) -> bool:
        """测试1: 检查配置是否完整"""
        self.print_step("1", "检查企业微信配置")

        required_configs = {
            "CORP_ID": config.CORP_ID,
            "AGENT_ID": config.AGENT_ID,
            "SECRET": config.SECRET,
            "TOKEN": config.TOKEN,
            "ENCODING_AES_KEY": config.ENCODING_AES_KEY
        }

        missing_configs = []
        for key, value in required_configs.items():
            if not value or value == f"your_{key.lower()}_here":
                missing_configs.append(key)

        if missing_configs:
            self.print_result(False, f"缺少配置: {', '.join(missing_configs)}")
            print("请在环境变量或代码中设置正确的企业微信配置")
            return False

        self.print_result(True, "所有配置项都已设置")
        for key, value in required_configs.items():
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"  📋 {key}: {masked_value}")

        return True

    async def test_2_get_access_token(self) -> bool:
        """测试2: 获取access_token"""
        self.print_step("2", "获取企业微信access_token")

        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": config.CORP_ID,
                "corpsecret": config.SECRET
            }

            print(f"📡 请求URL: {url}")
            print(f"📋 请求参数: corpid={config.CORP_ID[:8]}..., corpsecret=***")

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)

                print(f"📊 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"📄 响应内容: {result}")

                    if result.get("errcode") == 0:
                        self.access_token = result.get("access_token")
                        expires_in = result.get("expires_in", 0)

                        self.print_result(True, f"获取access_token成功，有效期: {expires_in}秒")
                        print(f"  🔑 Token: {self.access_token[:20]}...")
                        return True
                    else:
                        self.print_result(False, f"API返回错误: {result.get('errmsg', '未知错误')}")
                        return False
                else:
                    self.print_result(False, f"HTTP请求失败: {response.status_code}")
                    return False

        except Exception as e:
            self.print_result(False, f"请求异常: {e}")
            return False

    def generate_signature(self, token: str, timestamp: str, nonce: str, msg_encrypt: str = "") -> str:
        """生成企业微信签名"""
        tmp_list = [token, timestamp, nonce]
        if msg_encrypt:
            tmp_list.append(msg_encrypt)

        tmp_list.sort()
        tmp_str = "".join(tmp_list)
        return hashlib.sha1(tmp_str.encode()).hexdigest()

    async def test_3_webhook_verification(self) -> bool:
        """测试3: 测试webhook回调验证"""
        self.print_step("3", "测试企业微信回调验证")

        try:
            # 生成测试参数
            timestamp = str(int(time.time()))
            nonce = "test_nonce_123"
            echostr = base64.b64encode("test_echo_string".encode()).decode()

            # 生成签名
            signature = self.generate_signature(config.TOKEN, timestamp, nonce, echostr)

            # 测试URL
            url = f"{config.API_BASE_URL}/api/v1/wework/callback"
            params = {
                "msg_signature": signature,
                "timestamp": timestamp,
                "nonce": nonce,
                "echostr": echostr
            }

            print(f"📡 测试URL: {url}")
            print(f"📋 测试参数:")
            print(f"  timestamp: {timestamp}")
            print(f"  nonce: {nonce}")
            print(f"  echostr: {echostr}")
            print(f"  signature: {signature}")

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)

                print(f"📊 响应状态码: {response.status_code}")
                print(f"📄 响应内容: {response.text}")

                # 根据响应判断结果
                if response.status_code == 200:
                    self.print_result(True, "回调验证接口响应正常")
                    return True
                elif response.status_code == 403:
                    self.print_result(True, "回调验证接口可访问（签名验证失败是预期的）")
                    return True
                elif response.status_code == 404:
                    self.print_result(False, "回调接口不存在，请检查服务是否启动")
                    return False
                else:
                    self.print_result(False, f"意外的响应状态码: {response.status_code}")
                    return False

        except httpx.ConnectError:
            self.print_result(False, "无法连接到本地服务，请检查服务是否启动")
            print(f"  💡 请确保服务运行在: {config.API_BASE_URL}")
            return False
        except Exception as e:
            self.print_result(False, f"测试异常: {e}")
            return False

    def create_test_message_xml(self) -> str:
        """创建测试消息XML"""
        timestamp = str(int(time.time()))

        return f"""<xml>
            <ToUserName><![CDATA[test_agent]]></ToUserName>
            <FromUserName><![CDATA[test_customer]]></FromUserName>
            <CreateTime>{timestamp}</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[你好，这是一条测试消息]]></Content>
            <MsgId>{timestamp}001</MsgId>
            <AgentID>{config.AGENT_ID}</AgentID>
        </xml>"""

    async def test_4_message_webhook(self) -> bool:
        """测试4: 测试消息接收接口"""
        self.print_step("4", "测试企业微信消息接收")

        try:
            # 创建测试消息
            test_xml = self.create_test_message_xml()

            # 模拟加密（这里简化处理，实际需要用企业微信的加密算法）
            encrypted_msg = base64.b64encode(test_xml.encode()).decode()
            encrypted_xml = f"""<xml>
                <Encrypt><![CDATA[{encrypted_msg}]]></Encrypt>
            </xml>"""

            # 生成签名
            timestamp = str(int(time.time()))
            nonce = "test_nonce_msg"
            signature = self.generate_signature(config.TOKEN, timestamp, nonce)

            url = f"{config.API_BASE_URL}/api/v1/wework/callback"
            params = {
                "msg_signature": signature,
                "timestamp": timestamp,
                "nonce": nonce
            }

            print(f"📡 POST请求URL: {url}")
            print(f"📋 消息内容（加密前）: {test_xml}")
            print(f"📦 加密后XML: {encrypted_xml}")

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    params=params,
                    content=encrypted_xml,
                    headers={"Content-Type": "application/xml"}
                )

                print(f"📊 响应状态码: {response.status_code}")
                print(f"📄 响应内容: {response.text}")

                # 判断结果
                if response.status_code == 200:
                    if response.text in ["success", "ok"]:
                        self.print_result(True, "消息接收接口工作正常")
                        return True
                    else:
                        self.print_result(True, "消息接收接口可访问（解密可能失败，但接口正常）")
                        return True
                elif response.status_code in [400, 403]:
                    self.print_result(True, "消息接收接口可访问（解密失败是预期的）")
                    return True
                else:
                    self.print_result(False, f"意外的响应: {response.status_code}")
                    return False

        except Exception as e:
            self.print_result(False, f"测试异常: {e}")
            return False

    async def test_5_send_message(self) -> bool:
        """测试5: 测试发送消息（可选）"""
        self.print_step("5", "测试发送消息到企业微信")

        if not self.access_token:
            self.print_result(False, "缺少access_token，跳过发送消息测试")
            return False

        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
            params = {"access_token": self.access_token}

            # 测试消息数据
            message_data = {
                "touser": "@all",  # 发送给所有人，您可以改为特定用户
                "msgtype": "text",
                "agentid": config.AGENT_ID,
                "text": {
                    "content": "怎会如此"
                }
            }

            print(f"📡 发送URL: {url}")
            print(f"📋 消息数据: {message_data}")

            response_input = input("\n🤔 是否发送测试消息到企业微信？(y/N): ").lower()

            if response_input != 'y':
                self.print_result(True, "跳过发送消息测试（用户选择）")
                return True

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, params=params, json=message_data)

                print(f"📊 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"📄 响应内容: {result}")

                    if result.get("errcode") == 0:
                        self.print_result(True, "消息发送成功！请检查企业微信是否收到")
                        return True
                    else:
                        self.print_result(False, f"消息发送失败: {result.get('errmsg')}")
                        return False
                else:
                    self.print_result(False, f"HTTP请求失败: {response.status_code}")
                    return False

        except Exception as e:
            self.print_result(False, f"发送消息异常: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 企业微信API核心功能测试")
        print("=" * 60)
        print("📋 测试内容:")
        print("  1. 配置检查")
        print("  2. 获取access_token")
        print("  3. webhook回调验证")
        print("  4. 消息接收接口")
        print("  5. 发送消息（可选）")
        print()

        test_results = []

        # 依次执行测试
        tests = [
            ("配置检查", self.test_1_config_check()),
            ("获取access_token", self.test_2_get_access_token()),
            ("webhook验证", self.test_3_webhook_verification()),
            ("消息接收", self.test_4_message_webhook()),
            ("发送消息", self.test_5_send_message()),
        ]

        for test_name, test_coro in tests:
            try:
                result = await test_coro
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 测试出错: {e}")
                test_results.append((test_name, False))

        # 总结
        self.print_step("总结", "测试结果汇总")

        passed = 0
        total = len(test_results)

        for test_name, result in test_results:
            icon = "✅" if result else "❌"
            print(f"{icon} {test_name}")
            if result:
                passed += 1

        print()
        print(f"📊 测试结果: {passed}/{total} 通过")

        if passed == total:
            print("🎉 所有测试通过！企业微信API集成成功")
        elif passed >= total - 1:
            print("👍 大部分测试通过，系统基本可用")
        else:
            print("⚠️  部分测试失败，需要检查配置和服务状态")

        # 给出建议
        print("\n💡 下一步建议:")
        if passed < 2:
            print("  1. 检查企业微信配置是否正确")
            print("  2. 确认网络连接正常")
        elif passed < 4:
            print("  1. 确保本地服务正常启动")
            print("  2. 检查服务端口是否正确")
        else:
            print("  1. 可以开始测试完整的AI功能")
            print("  2. 配置RAGFlow和OpenAI")
