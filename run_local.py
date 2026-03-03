import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.application.graph.summary_graph import SummaryGraph

# ==========================================
# 硬编码
# ==========================================
TEST_GROUP_ID = 1017750994  # 你的测试群号
TEST_HOURS = 24  # 追溯小时数


# ==========================================

async def debug_session():
    print("🚀 [Debug] 正在加载本地配置进行测试...")
    load_dotenv()

    # 检查核心配置是否存在（优先使用通用 LLM_API_KEY，兼容 MOONSHOT_API_KEY）
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("❌ 错误: 没找到 LLM_API_KEY，请检查 .env 文件！")
        return

    graph = SummaryGraph()

    print(f"📡 正在请求数据 (群: {TEST_GROUP_ID}, 时间: {TEST_HOURS}h)...")

    start_time = asyncio.get_event_loop().time()

    try:
        # 调用核心逻辑
        result = await graph.invoke(TEST_GROUP_ID, TEST_HOURS)

        end_time = asyncio.get_event_loop().time()

        print("\n" + "—" * 30 + " 调试结果 " + "—" * 30)
        print(result if result else "⚠️ 无结果返回 (检查数据库消息是否存在)")
        print("—" * 69)
        print(f"⏱️  耗时: {end_time - start_time:.2f} 秒")

    except Exception as e:
        print(f"💥 奔溃了! 错误类型: {type(e).__name__}")
        print(f"具体原因: {e}")


if __name__ == "__main__":
    asyncio.run(debug_session())