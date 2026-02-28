import json
import pymysql
from typing import List, Dict
from ...storage.database.connection import get_connection


class EpisodicMemory:
    """事件记忆：存储具体的对话片段"""

    @staticmethod
    def add_episodic(
            group_id: int,
            message: List[Dict],
            summary: str,
            timestamp: int,
    ):
        conn = get_connection()
        cur = conn.cursor()

        sql = """
              INSERT INTO episodic_memory (group_id, messages_json, summary, timestamp)
              VALUES (%s, %s, %s, %s)
              """
        message_json = json.dumps(message, ensure_ascii=False)

        cur.execute(sql, (group_id, message_json, summary, timestamp))
        conn.commit()
        conn.close()
        conn.close()

    @staticmethod
    def get_episodic(
            group_id: int,
            limit: int = 5
    ) -> List[Dict]:
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
                'group_id': row['group_id'],
                'messages_json': json.loads(row['messages_json']),
                'summary': row['summary'],
                'timestamp': row['timestamp'],
                "created_at": row["created_at"].isoformat()
                    if row["created_at"] else None
            })

        return episodes



