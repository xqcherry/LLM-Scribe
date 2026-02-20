"""流式处理"""
from typing import AsyncIterator
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage


class StreamingHandler(AsyncCallbackHandler):
    """流式处理回调"""
    
    def __init__(self):
        self.tokens = []
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """收到新 token"""
        self.tokens.append(token)
    
    def get_content(self) -> str:
        """获取完整内容"""
        return "".join(self.tokens)


async def stream_summary(llm, prompt: list) -> AsyncIterator[str]:
    """流式生成摘要"""
    async for chunk in llm.astream(prompt):
        if hasattr(chunk, 'content'):
            yield chunk.content
        else:
            yield str(chunk)
