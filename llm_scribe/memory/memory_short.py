import json, pymysql
from llm_scribe.DB.connection import get_connection

# mem_json结构
STRUCTURE = {
    "concepts": [],
    "facts": [],
    "events": [],
    "quotes": [],
    "topics": [],
    "last_summary": "",
    "last_update_ts": None
}
# 加载短期记忆
def load_memory_short(group_id):
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT mem_json, last_check_ts, last_full_refresh_ts
        FROM memory_short WHERE group_id=%s
    """
    cur.execute(sql, (group_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {
            "mem_json": STRUCTURE.copy(),
            "last_check_ts": None,
            "last_full_refresh_ts": None
        }
    if not row["mem_json"]:
        semantic = STRUCTURE.copy()
    else:
        try:
            semantic = json.loads(row["mem_json"])
        except:
            semantic = STRUCTURE.copy()
    for key in STRUCTURE:
        semantic.setdefault(key, STRUCTURE[key])
    data = {
        "mem_json": semantic,
        "last_check_ts": row["last_check_ts"],
        "last_full_refresh_ts": row["last_full_refresh_ts"],
    } # 短期记忆格式
    return data
# 更新短期记忆
def save_memory_short(group_id, mem_json, full_refresh=False):
    conn = get_connection()
    cur = conn.cursor()
    # json To str
    mem_str = json.dumps(mem_json, ensure_ascii=False)

    if mem_json is not None:
        if full_refresh: # 记录last_full_refresh_ts, 后续做超时判断
            sql = """ 
                INSERT INTO memory_short(group_id, mem_json, last_check_ts, last_full_refresh_ts)
                VALUES(%s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    mem_json=VALUES(mem_json),
                    last_check_ts=NOW(),
                    last_full_refresh_ts=NOW()
            """
            cur.execute(sql, (group_id, mem_str))
        else:
            sql = """
                INSERT INTO memory_short(group_id, mem_json, last_check_ts, last_full_refresh_ts)
                VALUES(%s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    mem_json=VALUES(mem_json),
                    last_check_ts=NOW()
            """
            cur.execute(sql, (group_id, mem_str))
    else: # 不更新 mem_json，只更新时间戳
        sql = """
            INSERT INTO memory_short(group_id, mem_json, last_check_ts, last_full_refresh_ts)
            VALUES(%s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                last_check_ts=NOW()
        """
        cur.execute(sql, (group_id, "{}"))

    conn.commit()
    cur.close()
    conn.close()

