"""记忆压缩实现"""
from typing import List
from ...core.chains.compression_chain import CompressionChain


class MemoryCompressor:
    """记忆压缩器"""
    
    def __init__(self, llm):
        self.compression_chain = CompressionChain(llm)
    
    async def compress_summaries(
        self,
        summaries: List[str],
        max_length: int = 500
    ) -> str:
        """压缩多个摘要为一个"""
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0]
        
        # 使用压缩链
        compressed = await self.compression_chain.invoke(summaries)
        
        # 如果还是太长，截断
        if len(compressed) > max_length:
            compressed = compressed[:max_length] + "..."
        
        return compressed
    
    def should_compress(
        self,
        summaries: List[str],
        threshold: int = 5
    ) -> bool:
        """判断是否需要压缩"""
        return len(summaries) >= threshold
