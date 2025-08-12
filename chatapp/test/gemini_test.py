import pytest
import respx
import json
import time
from httpx import Response

from fastapi.testclient import TestClient
from chatapp.main import app  # 导入您的FastAPI应用实例
from chatapp.workers.ai_worker import _process_message_async  # 导入需要直接测试的异步函数
from chatapp.config import settings
from chatapp.services.session_manager import SessionManager

# 使用TestClient来模拟HTTP请求
client = TestClient(app)

# 定义一些测试中会用到的常量
TEST_AGENT_ID = "agent_li"
TEST_CUSTOMER_ID = "customer_zhang"
TEST_CORP_ID = settings.WEWORK_CORP_ID


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    """
    在每个测试函数运行前后执行的设置和清理操作
    """
    # --- 设置 (运行前) ---
    # 清理可能存在的旧会话，确保测试隔离
    session_manager = SessionManager()
    session_manager.clear_session(TEST_AGENT_ID, TEST_CUSTOMER_ID)
    print("\n--- Test session cleared ---")

    yield  # 这里是测试函数运行的地方

    # --- 清理 (运行后) ---
    session_manager.clear_session(TEST_AGENT_ID, TEST_CUSTOMER_ID)
    print("\n--- Test session cleaned up ---")


@pytest.mark.asyncio
@respx.mock
async def test_full_chat_flow():
    """
    测试一个完整的对话流程：
    1. 用户发送第一条消息 "你好"
    2. 验证系统处理和AI建议生成
    3. 用户发送第二条消息 "有三室两厅的户型吗？"
    4. 验证系统利用了第一条消息的上下文
    """

    # --- Mock外部API的响应 ---
    # 1. 模拟RAGFlow API
    ragflow_route = respx.post(f"{settings.RAGFLOW_API_URL}/api/v1/retrieval").mock(
        side_effect=[
            # 第一次调用 (对应 "你好")
            Response(200, json={"data": [{"content": "我们的房源很丰富，请问您有什么具体需求？"}]}),
            # 第二次调用 (对应 "三室两厅")
            Response(200, json={"data": [
                {"content": "阳光社区有一套120平米的三室两厅，总价约280万。"},
                {"content": "滨江花园有一套118平米的三室两厅，江景房，总价约310万。"}
            ]})
        ]
    )

    # 2. 模拟OpenAI API
    openai_route = respx.post(f"{settings.OPENAI_BASE_URL}/chat/completions").mock(
        side_effect=[
            # 第一次调用 (对应 "你好")
            Response(200, json={
                "choices": [{"message": {
                    "content": "建议1: 您好！欢迎咨询，请问有什么可以帮您的吗？\n建议2: 您好，很高兴为您服务！"}}]
            }),
            # 第二次调用 (对应 "三室两厅")
            Response(200, json={
                "choices": [{"message": {
                    "content": "建议1: 我们有几款不错的三室两厅户型，比如阳光社区120平米的和滨江花园118平米的，您对哪个更感兴趣？\n建议2: 当然有！我们有两款热门的三室两厅，总价在280万到310万之间，您预算大概多少？"}}]
            })
        ]
    )

    # --- 场景一: 用户发送第一条消息 ---
    print("\n--- SCENARIO 1: Customer sends first message ---")

    message_1 = {
        "msg_id": "test_msg_001",
        "from_user_name": TEST_CUSTOMER_ID,
        "to_user_name": TEST_AGENT_ID,
        "msg_type": "text",
        "content": "你好",
        "create_time": int(time.time())
    }

    # 直接调用AI Worker的核心处理函数来模拟Celery任务执行
    result_1 = await _process_message_async(message_1)

    # --- 验证场景一的结果 ---
    assert result_1 is not None
    assert result_1["customer_id"] == TEST_CUSTOMER_ID
    assert len(result_1["suggestions"]) == 2
    assert "您好！欢迎咨询" in result_1["suggestions"][0]
    # 验证API是否被正确调用
    assert ragflow_route.call_count == 1
    assert openai_route.call_count == 1
    # 验证会话上下文是否已创建
    session_manager = SessionManager()
    context_1 = session_manager.get_context(TEST_AGENT_ID, TEST_CUSTOMER_ID)
    assert len(context_1) == 1
    assert context_1[0]["content"] == "你好"

    # --- 场景二: 用户发送第二条消息（带上下文） ---
    print("\n--- SCENARIO 2: Customer sends follow-up message ---")

    message_2 = {
        "msg_id": "test_msg_002",
        "from_user_name": TEST_CUSTOMER_ID,
        "to_user_name": TEST_AGENT_ID,
        "msg_type": "text",
        "content": "有三室两厅的户型吗？",
        "create_time": int(time.time()) + 60
    }

    # 再次调用AI Worker的核心处理函数
    result_2 = await _process_message_async(message_2)

    # --- 验证场景二的结果 ---
    assert result_2 is not None
    assert len(result_2["suggestions"]) == 2
    assert "阳光社区" in result_2["suggestions"][0]  # 验证知识库信息是否被使用
    # 验证API调用次数是否增加
    assert ragflow_route.call_count == 2
    assert openai_route.call_count == 2
    # 验证会话上下文是否已更新
    context_2 = session_manager.get_context(TEST_AGENT_ID, TEST_CUSTOMER_ID)
    assert len(context_2) == 2
    assert context_2[0]["content"] == "你好"
    assert context_2[1]["content"] == "有三室两厅的户型吗？"

    # 获取传递给OpenAI的Prompt，验证其中是否包含了上下文
    last_openai_call = openai_route.calls.last
    prompt_json = json.loads(last_openai_call.request.content)
    prompt_text = prompt_json["messages"][0]["content"]
    assert "对话历史" in prompt_text
    assert "客户：你好" in prompt_text  # 验证上下午是否被正确传入

    print("\n--- ✅ Full chat flow test passed! ---")


def test_handle_non_text_message():
    """
    测试当收到非文本消息时，系统应跳过处理
    """
    print("\n--- SCENARIO 3: Handling non-text message ---")

    message_image = {
        "msg_id": "test_msg_003",
        "from_user_name": TEST_CUSTOMER_ID,
        "to_user_name": TEST_AGENT_ID,
        "msg_type": "image",  # 消息类型为图片
        "content": "",  # 图片消息content为空
        "pic_url": "http://example.com/image.jpg",
        "create_time": int(time.time())
    }

    # 因为 _process_message_async 是异步的，但这个测试本身不需要async/await
    # 我们可以用一个简单的包装来运行它
    import asyncio
    result = asyncio.run(_process_message_async(message_image))

    assert result["skipped"] is True
    assert result["reason"] == "non-text message"

    print("\n--- ✅ Non-text message test passed! ---")