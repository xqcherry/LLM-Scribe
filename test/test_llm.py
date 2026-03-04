import asyncio
from src.application.graph.summary_graph import SummaryGraph
from src.infrastructure.persistence.message_repository_impl import MySQLMessageRepository


async def test():
    # 明确只传 MySQL
    repo = MySQLMessageRepository()

    # 初始化时，llm_cache 和 memory_manager 默认为 None (或手动传 None)
    graph = SummaryGraph(
        message_repository=repo,
        llm_cache=None,
        memory_manager=None
    )

    # 填入一个你数据库里真实存在的群组 ID
    result = await graph.invoke(group_id=123, hours=24)
    print(result)


if __name__ == "__main__":
    asyncio.run(test())