# ============================================================================
# 主入口
# ============================================================================
import asyncio

from chatapp.test.quick import quick_test
from chatapp.test.test_qiyeapi import config, WeWorkAPITester

if __name__ == "__main__":
    import sys

    print("🤖 企业微信API测试工具")
    print()

    # 检查配置提示
    if config.CORP_ID == "your_corp_id_here":
        print("⚠️  请先配置企业微信参数！")
        print("方法1: 设置环境变量")
        print("  export WEWORK_CORP_ID='your_actual_corp_id'")
        print("  export WEWORK_AGENT_ID='your_actual_agent_id'")
        print("  # ... 其他配置")
        print()
        print("方法2: 直接修改代码中的WeWorkTestConfig类")
        print()

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_test())
    else:
        tester = WeWorkAPITester()
        asyncio.run(tester.run_all_tests())