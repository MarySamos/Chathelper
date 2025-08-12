# ============================================================================
# 快速测试脚本
# ============================================================================
from chatapp.test.test_qiyeapi import WeWorkAPITester


async def quick_test():
    """快速测试核心功能"""
    print("⚡ 快速测试模式")

    tester = WeWorkAPITester()

    # 只测试关键功能
    config_ok = await tester.test_1_config_check()
    if not config_ok:
        return

    token_ok = await tester.test_2_get_access_token()
    webhook_ok = await tester.test_3_webhook_verification()

    if token_ok and webhook_ok:
        print("\n✅ 核心功能测试通过！")
    else:
        print("\n❌ 核心功能测试失败")
