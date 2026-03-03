from typing import List

from src.application.chains.compression_chain import CompressionChain


class MemoryCompressor:
    """记忆压缩器"""

    def __init__(self, llm):
        self.compression_chain = CompressionChain(llm)

    async def compress_summaries(
        self,
        summaries: List[str],
        max_len: int = 500,
    ) -> str:
        if not summaries:
            return ""
        if len(summaries) == 1:
            return summaries[0]

        compressed = await self.compression_chain.invoke(summaries)

        if len(compressed) > max_len:
            compressed = compressed[:max_len] + "..."

        return compressed

    @staticmethod
    def is_compress(
        summaries: List[str],
        threshold: int = 5,
    ) -> bool:
        return len(summaries) >= threshold
