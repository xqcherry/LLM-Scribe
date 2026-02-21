"""事件记忆实现"""
import json
import pymysql
from typing import List, Dict
from ...storage.database.connection import get_connection


class EpisodicMemory:
    """事件记忆：存储具体的对话片段（持久化到 MySQL）"""
    
    def __init__(self):
        self._init_table()
    
    def _init_table(self):
        """初始化数据库表"""
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
        CREATE TABLE IF NOT EXISTS episodic_memory (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            messages_json TEXT NOT NULL,
            summary TEXT NOT NULL,
            timestamp INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_group_timestamp (group_id, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    
    def add_episode(
        self,
        group_id: int,
        messages: List[Dict],
        summary: str,
        timestamp: int
    ):
        """添加事件记忆"""
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
        INSERT INTO episodic_memory (group_id, messages_json, summary, timestamp)
        VALUES (%s, %s, %s, %s)
        """
        messages_json = json.dumps(messages, ensure_ascii=False)
        cur.execute(sql, (group_id, messages_json, summary, timestamp))
        conn.commit()
        cur.close()
        conn.close()
    
    def get_recent_episodes(
        self,
        group_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """获取最近的事件"""
        conn = get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
        SELECT group_id, messages_json, summary, timestamp, created_at
        FROM episodic_memory
        WHERE group_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        cur.execute(sql, (group_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        episodes = []
        for row in rows:
            episodes.append({
                "group_id": row["group_id"],
                "messages": json.loads(row["messages_json"]),
                "summary": row["summary"],
                "timestamp": row["timestamp"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })
        
        return episodes
