from __future__ import annotations

from typing import Dict, List

import aiomysql

from ....application.ports.message_repository_port import MessageRepositoryPort
from ..db_connection import get_pool


class MySQLMessageRepository(MessageRepositoryPort):
    """基于 aiomysql 连接池的异步消息仓储实现。"""

    async def get_group_messages(self, group_id: int, hours: int = 24) -> List[Dict]:
        pool = await get_pool()
        sql = """
            SELECT user_id, sender_nickname, raw_message, time
            FROM messages_event_logs
            WHERE message_type='group'
              AND group_id=%s
              AND time > UNIX_TIMESTAMP(NOW() - INTERVAL %s HOUR)
        """
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, (group_id, hours))
                rows = await cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def get_group_messages_after(self, group_id: int, timestamp: int) -> List[Dict]:
        pool = await get_pool()
        sql = """
            SELECT user_id, sender_nickname, raw_message, time
            FROM messages_event_logs
            WHERE message_type='group'
              AND group_id=%s
              AND time > %s
        """
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, (group_id, timestamp))
                rows = await cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(r: Dict) -> Dict:
        return {
            "user_id": r["user_id"],
            "sender_nickname": r["sender_nickname"],
            "raw_message": r["raw_message"],
            "time": r["time"],
        }
