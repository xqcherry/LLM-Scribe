import pymysql
from typing import List, Dict
from .connection import get_connection


class MessageRepository:
    """消息数据访问层"""

    @staticmethod
    def get_group_messages(group_id: int, hours: int = 24) -> List[Dict]:
        """获取群组消息"""
        conn = get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
            SELECT user_id, sender_nickname, raw_message, time
            FROM messages_event_logs
            WHERE message_type='group'
              AND group_id=%s
              AND time > UNIX_TIMESTAMP(NOW() - INTERVAL %s HOUR)
        """
        cur.execute(sql, (group_id, hours))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # 转换为字典列表
        cleaned = []
        for r in rows:
            cleaned.append({
                "user_id": r["user_id"],
                "sender_nickname": r["sender_nickname"],
                "raw_message": r["raw_message"],
                "time": r["time"]
            })
        
        return cleaned

    @staticmethod
    def get_group_messages_after(group_id: int, timestamp: int) -> List[Dict]:
        """获取指定时间之后的消息"""
        conn = get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
            SELECT user_id, sender_nickname, raw_message, time
            FROM messages_event_logs
            WHERE message_type='group'
              AND group_id=%s
              AND time > %s
        """
        cur.execute(sql, (group_id, timestamp))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(r) for r in rows]
