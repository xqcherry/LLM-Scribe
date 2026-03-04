import asyncio
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv


# --- 环境初始化 ---
def setup_environment():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    load_dotenv()


setup_environment()

# 导入业务组件
from src.application.graph.summary_graph import SummaryGraph

# --- 配置常量 ---
TEST_CONFIG = {
    "group_id": 1017750994,
    "hours": 24,
    "preview_limit": 15  # 增加预览量以便观察过滤效果
}


def print_divider(title: str):
    print(f"\n{'=' * 25} {title} {'=' * 25}")


async def run_debug_suite():
    print("🚀 [Debug] 正在启动数据清洗效果测试...")

    try:
        # 1. 初始化 Graph (它内部会通过 Impl 初始化我们的 FilterService)
        graph = SummaryGraph()
        group_id, hours = TEST_CONFIG["group_id"], TEST_CONFIG["hours"]

        # 2. 从数据库拉取原始数据
        print(f"📡 正在从数据库提取数据: 群 {group_id}...")
        raw_data = graph.message_repo.get_group_messages(group_id, hours)

        if not raw_data:
            print("⚠️ 数据库返回空数据，请检查 group_id 或时间范围。")
            return

        # 3. 使用你重构的 Service 进行清洗
        # 此时得到的 standard_lines 已经是 List[str]
        print(f"🧹 正在通过 MessageFilterService 进行清洗 (总计 {len(raw_data)} 条)...")
        standard_lines = graph.filter_service.get_standard_messages(raw_data)

        # 4. 对比展示
        print_divider("数据清洗样本对比")
        print(f"{'类型':<10} | {'内容'}")
        print("-" * 80)

        # 选取前 N 条原始数据看看它们变样了没
        for i in range(min(len(raw_data), TEST_CONFIG["preview_limit"])):
            msg = raw_data[i]
            uid = msg.get('user_id')
            raw_content = msg.get('raw_message', '').replace('\n', ' ')

            print(f"🔴 [RAW]    | [{uid}] {raw_content[:70]}...")

        print("-" * 80)

        # 5. 展示最终输出效果 (这是喂给 AI 的样子)
        print_divider("FINAL STANDARDIZED MESSAGES (FOR LLM)")
        if not standard_lines:
            print("❌ 所有消息均被过滤（黑名单/指令/长度不足）")
        else:
            # 打印前 20 条清洗后的结果
            for line in standard_lines[:20]:
                print(f"🟢 {line}")

            if len(standard_lines) > 20:
                print(f"\n... (还有 {len(standard_lines) - 20} 条消息已省略)")

        print_divider("统计汇总")
        print(f"原始消息总数: {len(raw_data)}")
        print(f"有效标准行数: {len(standard_lines)}")
        print(f"过滤掉的噪音: {len(raw_data) - len(standard_lines)}")
        print("=" * 65)

    except Exception as e:
        print(f"💥 运行异常: {e}")
        import traceback;
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_debug_suite())