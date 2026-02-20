"""语义分块器"""
from langchain.text_splitter import SemanticChunker as LangChainSemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List, Dict


class SemanticChunker:
    """语义分块器，按语义边界而非固定大小分块"""
    
    def __init__(self):
        # 使用本地 Embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.chunker = LangChainSemanticChunker(
            self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95
        )
    
    def chunk_messages(
        self,
        messages: List[Dict],
        max_chunk_size: int = 200
    ) -> List[List[Dict]]:
        """将消息列表按语义分块"""
        # 将消息转换为文本
        text = "\n".join(
            f"{m.get('sender_nickname', '')}: {m.get('raw_message', '')}"
            for m in messages
        )
        
        # 语义分块
        text_chunks = self.chunker.split_text(text)
        
        # 将文本块映射回消息块（简化实现）
        # 实际应该更精确地映射
        message_chunks = []
        current_chunk = []
        current_text = ""
        
        for msg in messages:
            msg_text = f"{msg.get('sender_nickname', '')}: {msg.get('raw_message', '')}\n"
            
            if len(current_chunk) >= max_chunk_size:
                message_chunks.append(current_chunk)
                current_chunk = [msg]
                current_text = msg_text
            else:
                current_chunk.append(msg)
                current_text += msg_text
        
        if current_chunk:
            message_chunks.append(current_chunk)
        
        return message_chunks
