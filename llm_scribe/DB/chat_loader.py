from llm_scribe.DB.connection import get_connection
from llm_scribe.utils import CQ_filter
import pymysql
# 从群获取信息
def get_group_msg(group_id, hours: int = 24):
    conn = get_connection() # 数据库连接
    cur = conn.cursor(pymysql.cursors.DictCursor) # 字典游标
    sql = """
        SELECT user_id, sender_nickname, raw_message, time
        FROM messages_event_logs
        WHERE message_type='group'
          AND group_id=%s
          AND time > UNIX_TIMESTAMP(NOW() - INTERVAL %s HOUR)
        ORDER BY time ASC
    """
    cur.execute(sql, (group_id, hours))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    cleaned = []
    for r in rows: # 过滤CQ字样
        text = CQ_filter(r["raw_message"])
        if text.strip():
            r["raw_message"] = text
            cleaned.append(r)

    return cleaned
