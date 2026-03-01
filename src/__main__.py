import asyncio
from llm_scribe.core.graph import SummaryGraph

if __name__ == "__main__":
    group_id = 123454325
    hours = 23
    print(f"[LLM-Scribe] 独立运行模式启动 (group_id={group_id}, hours={hours})")
    
    async def main():
        graph = SummaryGraph()
        result = await graph.invoke(group_id, hours)
        print("\n=== 摘要结果 ===\n")
        print(result or "（无输出或模型未配置）")
    
    asyncio.run(main())