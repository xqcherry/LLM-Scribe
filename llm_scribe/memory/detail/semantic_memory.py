"""语义记忆实现"""
import json
import pymysql
from typing import List, Dict
from ...storage.database.connection import get_connection


class SemanticMemory:
    """语义记忆：提取的概念和知识（持久化到 MySQL）"""
    
    def __init__(self):
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = get_connection()
        cur = conn.cursor()
        
        # 概念表
        sql_concepts = """
        CREATE TABLE IF NOT EXISTS semantic_concepts (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            concept VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_group_concept (group_id, concept),
            INDEX idx_group (group_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cur.execute(sql_concepts)
        
        # 事件表
        sql_events = """
        CREATE TABLE IF NOT EXISTS semantic_events (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            event TEXT NOT NULL,
            participants_json TEXT,
            timestamp INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_group_timestamp (group_id, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cur.execute(sql_events)
        
        conn.commit()
        cur.close()
        conn.close()
    
    def add_concepts(self, group_id: int, concepts: List[str]):
        """添加概念"""
        if not concepts:
            return
        
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
        INSERT IGNORE INTO semantic_concepts (group_id, concept)
        VALUES (%s, %s)
        """
        for concept in concepts:
            cur.execute(sql, (group_id, concept))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def add_event(
        self,
        group_id: int,
        event: str,
        participants: List[str],
        timestamp: int
    ):
        """添加事件"""
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
        INSERT INTO semantic_events (group_id, event, participants_json, timestamp)
        VALUES (%s, %s, %s, %s)
        """
        participants_json = json.dumps(participants, ensure_ascii=False) if participants else None
        cur.execute(sql, (group_id, event, participants_json, timestamp))
        conn.commit()
        cur.close()
        conn.close()
    
    def get_concepts(self, group_id: int) -> List[str]:
        """获取概念列表"""
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
        SELECT DISTINCT concept
        FROM semantic_concepts
        WHERE group_id = %s
        ORDER BY created_at DESC
        """
        cur.execute(sql, (group_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [row[0] for row in rows]
    
    def get_recent_events(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """获取最近事件"""
        conn = get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
        SELECT group_id, event, participants_json, timestamp, created_at
        FROM semantic_events
        WHERE group_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        cur.execute(sql, (group_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        events = []
        for row in rows:
            participants = json.loads(row["participants_json"]) if row["participants_json"] else []
            events.append({
                "event": row["event"],
                "participants": participants,
                "timestamp": row["timestamp"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })
        
        return events
