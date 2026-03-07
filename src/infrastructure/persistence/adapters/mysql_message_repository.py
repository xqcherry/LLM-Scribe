from __future__ import annotations

from typing import Dict, List

import pymysql

from src.application.ports.message_repository_port import MessageRepositoryPort
from src.infrastructure.persistence.db_connection import get_connection


class MySQLMessageRepository(MessageRepositoryPort):
    """基于 MySQL 的消息仓储实现。"""

    def get_group_messages(self, group_id: int, hours: int = 24) -> List[Dict]:
        """获取群组消息。"""
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

        cleaned: List[Dict] = []
        for r in rows:
            cleaned.append(
                {
                    "user_id": r["user_id"],
                    "sender_nickname": r["sender_nickname"],
                    "raw_message": r["raw_message"],
                    "time": r["time"],
                }
            )

        return cleaned

    def get_group_messages_after(self, group_id: int, timestamp: int) -> List[Dict]:
        """获取指定时间之后的消息。"""
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


