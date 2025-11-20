import json, pymysql
from ..DB.connection import get_connection

def load_chat_cache(group_id):
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT msg_json, start_ts, end_ts
        FROM chat_cache WHERE group_id=%s
    """
    cur.execute(sql, (group_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None
    data = {
        "msgs": json.loads(row["msg_json"]),
        "start_ts": row["start_ts"],
        "end_ts": row["end_ts"],
    } # dict
    return data

def save_chat_cache(group_id, msgs, start_ts, end_ts):
    conn = get_connection()
    cur = conn.cursor()
    sql = """
        INSERT INTO chat_cache(group_id, msg_json, start_ts, end_ts)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            msg_json=VALUES(msg_json),
            start_ts=VALUES(start_ts),
            end_ts=VALUES(end_ts),
            updated_at=NOW()
    """
    cur.execute(sql, (group_id, json.dumps(msgs, ensure_ascii=False), start_ts, end_ts))
    conn.commit()
    cur.close()
    conn.close()

def get_group_msg_after(group_id, last_ts):
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT user_id, sender_nickname, raw_message, time
        FROM messages_event_logs
        WHERE group_id=%s AND time > %s
        ORDER BY time
    """
    cur.execute(sql, (group_id, last_ts))
    return cur.fetchall()
