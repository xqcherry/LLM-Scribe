import asyncio
import json
import traceback
from src.application.graph.summary_graph import SummaryGraph
from src.infrastructure.persistence.message_repository_impl import MySQLMessageRepository

async def test():
    # 1. 初始化
    repo = MySQLMessageRepository()
    graph = SummaryGraph(
        message_repository=repo,
        llm_cache=None,
        memory_manager=None
    )

    print("🚀 正在请求完整数据流水线...")

    try:
        # 调用 Graph
        state = await graph.invoke(group_id=1017750994, hours=24)

        # A. 显示排版后的完整摘要 (这里本来就是完整的)
        print("\n" + " ✨ 最终生成完整摘要 ".center(60, "="))
        print(state["summary"])

        # B. 显示结构化话题的完整内容 (去掉了 [:60] 限制)
        print("\n" + " 📅 完整话题列表 (Topics) ".center(60, "="))
        topics = state.get("topics", [])
        for i, topic in enumerate(topics, 1):
            print(f"\n话题 {i}: 【{topic.get('topic')}】")
            print(f"参与者: {', '.join(map(str, topic.get('contributors', [])))}")
            print(f"详细内容: {topic.get('detail')}") # 这里现在会完整显示，不截断

        # C. 显示元数据的原始结构 (用于排查字段是否完整)
        print("\n" + " 📦 原始 Metadata JSON ".center(60, "="))
        # 排除 analysis_result 这种复杂对象，只看基础字段
        printable_meta = {k: v for k, v in state["metadata"].items() if k != "analysis_result"}
        print(json.dumps(printable_meta, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ 运行失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())